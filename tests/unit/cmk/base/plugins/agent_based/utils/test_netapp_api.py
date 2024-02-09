#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import pytest

from cmk.base.plugins.agent_based.agent_based_api.v1 import render, Result, Service, State
from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
    StringTable,
)
from cmk.base.plugins.agent_based.utils.netapp_api import (
    check_netapp_luns,
    check_netapp_qtree_quota,
    discover_netapp_qtree_quota,
    get_single_check,
    get_summary_check,
    parse_netapp_api_multiple_instances,
    Qtree,
    SectionMultipleInstances,
)

pytestmark = pytest.mark.checks
LAST_TIME_EPOCH = (
    datetime.strptime("1988-06-08 16:00:00.000000", "%Y-%m-%d %H:%M:%S.%f") - datetime(1970, 1, 1)
).total_seconds()


@pytest.mark.parametrize(
    "info, expected_result",
    [
        (
            [
                [
                    "interface e0a",
                    "mediatype auto-1000t-fd-up",
                    "flowcontrol full",
                    "mtusize 9000",
                    "ipspace-name default-ipspace",
                    "mac-address 01:b0:89:22:df:01",
                ],
                ["interface"],
            ],
            {
                "e0a": [
                    {
                        "interface": "e0a",
                        "mediatype": "auto-1000t-fd-up",
                        "flowcontrol": "full",
                        "mtusize": "9000",
                        "ipspace-name": "default-ipspace",
                        "mac-address": "01:b0:89:22:df:01",
                    }
                ]
            },
        )
    ],
)
def test_parse_netapp_api_multiple_instances(
    info: StringTable, expected_result: SectionMultipleInstances
) -> None:
    result = parse_netapp_api_multiple_instances(info)
    assert result == expected_result


@pytest.mark.parametrize(
    "item, online, read_only, params",
    [
        pytest.param(
            "lun1",
            True,
            False,
            {
                "levels": (80.0, 90.0),  # warn/crit in percent
                "trend_range": 24,
                "trend_perfdata": True,  # do send performance data for trends
                "read_only": False,
                "ignore_levels": False,
            },
        ),
        pytest.param(
            "lun1",
            True,
            False,
            {
                "levels": (80.0, 90.0),
                "trend_range": 24,
                "trend_perfdata": True,
                "read_only": True,
            },
        ),
        pytest.param(
            "lun1",
            True,
            False,
            {
                "levels": (80.0, 90.0),
                "trend_range": 24,
                "trend_perfdata": True,
                "read_only": False,
                "ignore_levels": True,
            },
        ),
    ],
)
def test_check_netapp_luns(
    item: str,
    online: bool,
    read_only: bool,
    params: Mapping[str, Any],
) -> None:
    NOW_SIMULATED_SECONDS = (
        datetime.strptime("1988-06-08 17:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
        - datetime(1970, 1, 1)
    ).total_seconds()

    result = list(
        check_netapp_luns(
            item,
            online,
            read_only,
            500_000_000,
            0,
            0,
            NOW_SIMULATED_SECONDS,
            {"lun1.delta": (LAST_TIME_EPOCH, 0.0)},
            params,
        )
    )

    result_item = 0
    if read_only != params.get("read_only"):
        assert isinstance(result[0], Result)
        assert result[0].state == State.WARN
        result_item += 1

    if params.get("ignore_levels"):
        assert result[result_item] == Result(
            state=State.OK, summary=f"Total size: {render.bytes(500_000_000)}"
        )
        result_item += 1
        assert result[result_item] == Result(state=State.OK, summary="Used space is ignored")


_FANS_SECTION = {
    "fan1": {"cooling-element-is-error": "true", "cooling-element-number": "3"},
    "fan2": {"cooling-element-is-error": "false", "cooling-element-number": "4"},
}


@pytest.mark.parametrize(
    "item_name, expected_result",
    [
        pytest.param(
            "fan1", [Result(state=State.CRIT, summary="Error in fan 3")], id="fan in error"
        ),
        pytest.param("fan2", [Result(state=State.OK, summary="Operational state OK")], id="fan ok"),
    ],
)
def test_get_single_check_fan(item_name: str, expected_result: CheckResult) -> None:
    result = list(get_single_check("fan")(item_name, _FANS_SECTION))

    assert result == expected_result


def test_get_summary_check_fan() -> None:
    result = list(get_summary_check("fan")("", _FANS_SECTION))

    assert result == [
        Result(state=State.OK, summary="OK: 1 of 2"),
        Result(state=State.CRIT, summary="Failed: 1 (fan1)"),
    ]


_PSU_SECTION = {
    "psu1": {"power-supply-is-error": "true", "power-supply-element-number": "3"},
    "psu2": {"power-supply-is-error": "false", "power-supply-element-number": "4"},
}


@pytest.mark.parametrize(
    "item_name, expected_result",
    [
        pytest.param(
            "psu1",
            [Result(state=State.CRIT, summary="Error in power supply unit 3")],
            id="psu in error",
        ),
        pytest.param("psu2", [Result(state=State.OK, summary="Operational state OK")], id="psu ok"),
    ],
)
def test_get_single_check_psu(item_name: str, expected_result: CheckResult) -> None:
    result = list(get_single_check("power supply unit")(item_name, _PSU_SECTION))

    assert result == expected_result


def test_get_summary_check_psu() -> None:
    result = list(get_summary_check("power supply unit")("", _PSU_SECTION))

    assert result == [
        Result(state=State.OK, summary="OK: 1 of 2"),
        Result(state=State.CRIT, summary="Failed: 1 (psu1)"),
    ]


_QTREE_SECTION = {
    # discovered as "qtree.1"
    "qtree.1": Qtree(
        quota="qtree",
        quota_users="1",
        quota_type="type",
        volume="",
        disk_limit="500",
        disk_used="100",
        files_used="",
        file_limit="",
    ),
    # discovered as "volume_name/qtree.2" with exclude_volume to False
    "volume_name/qtree.2": Qtree(
        quota="qtree",
        quota_users="2",
        quota_type="type",
        volume="volume_name",
        disk_limit="500",
        disk_used="100",
        files_used="",
        file_limit="",
    ),
    # discovered as "qtree.2" with exclude_volume to True
    "qtree.2": Qtree(
        quota="qtree",
        quota_users="2",
        quota_type="type",
        volume="volume_name",
        disk_limit="500",
        disk_used="100",
        files_used="",
        file_limit="",
    ),
}


@pytest.mark.parametrize(
    "params, expected_result",
    [
        pytest.param(
            {},  # {"exclude_volume": False},
            [Service(item="qtree.1"), Service(item="volume_name/qtree.2")],
            id="",
        ),
        pytest.param(
            {"exclude_volume": True},
            [Service(item="qtree.1"), Service(item="qtree.2")],
            id="",
        ),
    ],
)
def test_discover_netapp_qtree_quota(
    params: Mapping[str, Any], expected_result: DiscoveryResult
) -> None:
    result = list(discover_netapp_qtree_quota(params, _QTREE_SECTION))
    assert result == expected_result


def test_check_netapp_qtree_quota_ok() -> None:
    value_store = {"item_name.delta": (LAST_TIME_EPOCH, 0.0)}
    qtree = Qtree(
        quota="qtree",
        quota_users="1",
        quota_type="type",
        volume="",
        disk_limit="500",
        disk_used="100",
        files_used="",
        file_limit="",
    )
    params = {
        "levels": (80.0, 90.0),
        "trend_range": 24,
        "trend_perfdata": True,
    }
    result = list(check_netapp_qtree_quota("item_name", qtree, params, value_store))

    assert len(result) == 10


@pytest.mark.parametrize(
    "qtree, expected_result",
    [
        pytest.param(
            Qtree(
                quota="qtree",
                quota_users="2",
                quota_type="type",
                volume="volume_name",
                disk_limit="",
                disk_used="100",
                files_used="",
                file_limit="",
            ),
            [Result(state=State.UNKNOWN, summary="Qtree has no disk limit set")],
            id="qtree with no disk limit",
        ),
        pytest.param(
            Qtree(
                quota="qtree",
                quota_users="2",
                quota_type="type",
                volume="volume_name",
                disk_limit="500",
                disk_used="unknown",
                files_used="",
                file_limit="",
            ),
            [Result(state=State.UNKNOWN, summary="Qtree has no used space data set")],
            id="qtree with no disk used",
        ),
    ],
)
def test_check_netapp_qtree_quota_unknown(qtree: Qtree, expected_result: CheckResult) -> None:
    result = list(check_netapp_qtree_quota("item_name", qtree, {}, {}))

    assert result == expected_result
