#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import itertools
from collections.abc import Container, Iterable, Iterator, Mapping, MutableMapping, Sequence

import cmk.utils.debug
import cmk.utils.misc
import cmk.utils.paths
from cmk.utils.check_utils import unwrap_parameters
from cmk.utils.exceptions import MKGeneralException, MKTimeout, OnError
from cmk.utils.log import console, section
from cmk.utils.type_defs import CheckPluginName, HostName, ParsedSectionName, ServiceID

from cmk.fetchers import SourceType

from cmk.checkers import HostKey, plugin_contexts
from cmk.checkers.discovery import AutocheckEntry, AutochecksStore

import cmk.base.config as config
from cmk.base.agent_based.data_provider import ParsedSectionsBroker
from cmk.base.agent_based.utils import get_section_kwargs
from cmk.base.api.agent_based.checking_classes import CheckPlugin
from cmk.base.config import ConfigCache

from .utils import QualifiedDiscovery


def analyse_discovered_services(
    config_cache: ConfigCache,
    host_name: HostName,
    *,
    parsed_sections_broker: ParsedSectionsBroker,
    check_plugins: Mapping[CheckPluginName, CheckPlugin],
    run_plugin_names: Container[CheckPluginName],
    forget_existing: bool,
    keep_vanished: bool,
    on_error: OnError,
) -> QualifiedDiscovery[AutocheckEntry]:

    return _analyse_discovered_services(
        existing_services=AutochecksStore(host_name).read(),
        discovered_services=_discover_services(
            config_cache,
            host_name,
            parsed_sections_broker=parsed_sections_broker,
            check_plugins=check_plugins,
            run_plugin_names=run_plugin_names,
            on_error=on_error,
        ),
        run_plugin_names=run_plugin_names,
        forget_existing=forget_existing,
        keep_vanished=keep_vanished,
    )


def _analyse_discovered_services(
    *,
    existing_services: Sequence[AutocheckEntry],
    discovered_services: list[AutocheckEntry],
    run_plugin_names: Container[CheckPluginName],
    forget_existing: bool,
    keep_vanished: bool,
) -> QualifiedDiscovery[AutocheckEntry]:

    return QualifiedDiscovery(
        preexisting=_services_to_remember(
            choose_from=existing_services,
            run_plugin_names=run_plugin_names,
            forget_existing=forget_existing,
        ),
        current=discovered_services
        + _services_to_keep(
            choose_from=existing_services,
            run_plugin_names=run_plugin_names,
            keep_vanished=keep_vanished,
        ),
        key=lambda s: s.id(),
    )


def _services_to_remember(
    *,
    choose_from: Sequence[AutocheckEntry],
    run_plugin_names: Container[CheckPluginName],
    forget_existing: bool,
) -> Sequence[AutocheckEntry]:
    """Compile a list of services to regard as being the last known state

    This list is used to classify services into new/old/vanished.
    Remembering is not the same as keeping!
    Always remember the services of plugins that are not being run.
    """
    return _drop_plugins_services(choose_from, run_plugin_names) if forget_existing else choose_from


def _services_to_keep(
    *,
    choose_from: Sequence[AutocheckEntry],
    run_plugin_names: Container[CheckPluginName],
    keep_vanished: bool,
) -> list[AutocheckEntry]:
    """Compile a list of services to keep in addition to the discovered ones

    These services are considered to be currently present (even if they are not discovered).
    Always keep the services of plugins that are not being run.
    """
    return (
        list(choose_from)
        if keep_vanished
        else _drop_plugins_services(choose_from, run_plugin_names)
    )


def _drop_plugins_services(
    services: Sequence[AutocheckEntry],
    plugin_names: Container[CheckPluginName],
) -> list[AutocheckEntry]:
    return [s for s in services if s.check_plugin_name not in plugin_names]


def _discover_services(
    config_cache: ConfigCache,
    host_name: HostName,
    *,
    parsed_sections_broker: ParsedSectionsBroker,
    run_plugin_names: Container[CheckPluginName],
    check_plugins: Mapping[CheckPluginName, CheckPlugin],
    on_error: OnError,
) -> list[AutocheckEntry]:
    # find out which plugins we need to discover
    plugin_candidates = _find_candidates(
        parsed_sections_broker,
        run_plugin_names,
        check_plugins,
    )
    section.section_step("Executing discovery plugins (%d)" % len(plugin_candidates))
    console.vverbose("  Trying discovery with: %s\n" % ", ".join(str(n) for n in plugin_candidates))
    # The host name must be set for the host_name() calls commonly used to determine the
    # host name for host_extra_conf{_merged,} calls in the legacy checks.

    service_table: MutableMapping[ServiceID, AutocheckEntry] = {}
    try:
        with plugin_contexts.current_host(host_name):
            for check_plugin_name in plugin_candidates:
                try:
                    service_table.update(
                        {
                            entry.id(): entry
                            for entry in _discover_plugins_services(
                                config_cache,
                                check_plugin_name=check_plugin_name,
                                check_plugins=check_plugins,
                                host_key=HostKey(
                                    host_name,
                                    (
                                        SourceType.MANAGEMENT
                                        if check_plugin_name.is_management_name()
                                        else SourceType.HOST
                                    ),
                                ),
                                parsed_sections_broker=parsed_sections_broker,
                                on_error=on_error,
                            )
                        }
                    )
                except (KeyboardInterrupt, MKTimeout):
                    raise
                except Exception as e:
                    if on_error is OnError.RAISE:
                        raise
                    if on_error is OnError.WARN:
                        console.error(f"Discovery of '{check_plugin_name}' failed: {e}\n")

            return list(service_table.values())

    except KeyboardInterrupt:
        raise MKGeneralException("Interrupted by Ctrl-C.")


def _find_candidates(
    broker: ParsedSectionsBroker,
    run_plugin_names: Container[CheckPluginName],
    check_plugins: Mapping[CheckPluginName, CheckPlugin],
) -> set[CheckPluginName]:
    """Return names of check plugins that this multi_host_section may
    contain data for.

    Given this mutli_host_section, there is no point in trying to discover
    any check plugins not returned by this function.  This does not
    address the question whether or not the returned check plugins will
    discover something.

    We have to consider both the host, and the management board as source
    type. Note that the determination of the plugin names is not quite
    symmetric: For the host, we filter out all management plugins,
    for the management board we create management variants from all
    plugins that are not already designed for management boards.

    """
    preliminary_candidates: Sequence[tuple[CheckPluginName, list[ParsedSectionName]]] = list(
        (p.name, p.sections) for p in check_plugins.values() if p.name in run_plugin_names
    )

    # Flattened list of ParsedSectionName, optimization only.
    parsed_sections_of_interest: Sequence[ParsedSectionName] = list(
        frozenset(
            itertools.chain.from_iterable(sections for (_name, sections) in preliminary_candidates)
        )
    )

    return _find_host_candidates(
        broker, preliminary_candidates, parsed_sections_of_interest
    ) | _find_mgmt_candidates(broker, preliminary_candidates, parsed_sections_of_interest)


def _find_host_candidates(
    broker: ParsedSectionsBroker,
    preliminary_candidates: Iterable[tuple[CheckPluginName, list[ParsedSectionName]]],
    parsed_sections_of_interest: Iterable[ParsedSectionName],
) -> set[CheckPluginName]:

    available_parsed_sections = broker.filter_available(
        parsed_sections_of_interest,
        SourceType.HOST,
    )

    return {
        name
        for (name, sections) in preliminary_candidates
        # *filter out* all names of management only check plugins
        if not name.is_management_name()
        and any(section in available_parsed_sections for section in sections)
    }


def _find_mgmt_candidates(
    broker: ParsedSectionsBroker,
    preliminary_candidates: Iterable[tuple[CheckPluginName, list[ParsedSectionName]]],
    parsed_sections_of_interest: Iterable[ParsedSectionName],
) -> set[CheckPluginName]:

    available_parsed_sections = broker.filter_available(
        parsed_sections_of_interest,
        SourceType.MANAGEMENT,
    )

    return {
        # *create* all management only names of the plugins
        name.create_management_name()
        for (name, sections) in preliminary_candidates
        if any(section in available_parsed_sections for section in sections)
    }


def _discover_plugins_services(
    config_cache: ConfigCache,
    *,
    check_plugin_name: CheckPluginName,
    check_plugins: Mapping[CheckPluginName, CheckPlugin],
    host_key: HostKey,
    parsed_sections_broker: ParsedSectionsBroker,
    on_error: OnError,
) -> Iterator[AutocheckEntry]:
    # Skip this check type if is ignored for that host
    if config_cache.check_plugin_ignored(host_key.hostname, check_plugin_name):
        console.vverbose("  Skip ignored check plugin name '%s'\n" % check_plugin_name)
        return

    try:
        check_plugin = check_plugins[check_plugin_name]
    except KeyError:
        console.warning("  Missing check plugin: '%s'\n" % check_plugin_name)
        return

    try:
        kwargs = get_section_kwargs(parsed_sections_broker, host_key, check_plugin.sections)
    except Exception as exc:
        if cmk.utils.debug.enabled() or on_error is OnError.RAISE:
            raise
        if on_error is OnError.WARN:
            console.warning("  Exception while parsing agent section: %s\n" % exc)
        return

    if not kwargs:
        return

    disco_params = config.get_discovery_parameters(host_key.hostname, check_plugin)
    if disco_params is not None:
        kwargs = {**kwargs, "params": disco_params}

    try:
        yield from (
            AutocheckEntry(
                check_plugin_name=check_plugin.name,
                item=service.item,
                parameters=unwrap_parameters(service.parameters),
                # Convert from APIs ServiceLabel to internal ServiceLabel
                service_labels={label.name: label.value for label in service.labels},
            )
            for service in check_plugin.discovery_function(**kwargs)
        )
    except Exception as e:
        if on_error is OnError.RAISE:
            raise
        if on_error is OnError.WARN:
            console.warning(
                "  Exception in discovery function of check plugin '%s': %s"
                % (check_plugin.name, e)
            )
