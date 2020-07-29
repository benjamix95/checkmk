#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""Page menu processing

Cares about the page navigation of our GUI. This is the menu bar that can be found on top of each
page. It is meant to be used for page wide actions and navigation to other related pages.

The hierarchy here is:

    PageMenu > PageMenuDropdown > PageMenuTopic > PageMenuEntry > ABCPageMenuItem
"""

import abc
import json
from dataclasses import dataclass, field
from typing import List, Iterator, Optional

from cmk.gui.i18n import _
from cmk.gui.globals import html


def enable_page_menu_entry(name):
    _toggle_page_menu_entry(name, state=True)


def disable_page_menu_entry(name):
    _toggle_page_menu_entry(name, state=False)


def _toggle_page_menu_entry(name: str, state: bool) -> None:
    html.javascript("cmk.page_menu.enable_menu_entry(%s, %s)" %
                    (json.dumps(name), json.dumps(state)))


@dataclass
class Link:
    """Group of attributes used for linking"""
    url: Optional[str] = None
    target: Optional[str] = None
    onclick: Optional[str] = None


class ABCPageMenuItem(metaclass=abc.ABCMeta):
    """Base class for all page menu items of the page menu
    There can be different item types, like regular links, search fields, ...
    """


@dataclass
class PageMenuLink(ABCPageMenuItem):
    """A generic hyper link to other pages"""
    link: Link


def make_simple_link(url: str) -> PageMenuLink:
    return PageMenuLink(Link(url=url))


def make_external_link(url: str) -> PageMenuLink:
    return PageMenuLink(Link(url=url, target="_blank"))


def make_javascript_link(javascript: str) -> PageMenuLink:
    return PageMenuLink(Link(onclick=javascript))


def make_form_submit_link(form_name: str, button_name: str) -> PageMenuLink:
    return make_javascript_link("cmk.page_menu.form_submit(%s, %s)" %
                                (json.dumps(form_name), json.dumps(button_name)))


@dataclass
class PageMenuEntry:
    """Representing an entry in the menu, holding the ABCPageMenuItem to be displayed"""
    title: str
    icon_name: str
    item: ABCPageMenuItem
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: bool = True
    is_advanced: bool = False
    is_list_entry: bool = True
    is_shortcut: bool = False
    is_suggested: bool = False


@dataclass
class PageMenuTopic:
    """A dropdown is populated with multiple topics which hold the actual entries"""
    title: str
    entries: List[PageMenuEntry] = field(default_factory=list)


@dataclass
class PageMenuDropdown:
    """Each dropdown in the page menu is represented by this structure"""
    name: str
    title: str
    topics: List[PageMenuTopic] = field(default_factory=list)

    @property
    def any_advanced_entries(self) -> bool:
        return any(entry.is_advanced for topic in self.topics for entry in topic.entries)

    @property
    def is_empty(self) -> bool:
        return not any(entry.is_list_entry for topic in self.topics for entry in topic.entries)


@dataclass
class PageMenu:
    """Representing the whole menu of the page"""
    dropdowns: List[PageMenuDropdown] = field(default_factory=list)

    def __post_init__(self):
        if self.dropdowns:
            # Add the display options dropdown
            self.dropdowns.append(make_display_options_dropdown())

            # Add the help dropdown, which shall be shown on all pages
            self.dropdowns.append(make_help_dropdown())

    @property
    def shortcuts(self) -> Iterator[PageMenuEntry]:
        has_suggestions = False
        for dropdown in self.dropdowns:
            for topic in dropdown.topics:
                for entry in topic.entries:
                    if entry.is_shortcut:
                        if entry.is_suggested:
                            has_suggestions = True

                        yield entry

        if has_suggestions:
            yield PageMenuEntry(
                title=_("Toggle suggested actions"),
                icon_name="suggestion",
                item=make_javascript_link("cmk.page_menu.toggle_suggestions()"),
                name="toggle_suggestions",
            )

    @property
    def suggestions(self) -> Iterator[PageMenuEntry]:
        for entry in self.shortcuts:
            if entry.is_suggested:
                yield entry

    @property
    def has_suggestions(self) -> bool:
        return any(True for _s in self.suggestions)


def make_display_options_dropdown() -> PageMenuDropdown:
    return PageMenuDropdown(
        name="display",
        title=_("Display"),
        topics=[
            PageMenuTopic(
                title=_("General display options"),
                entries=[
                    PageMenuEntry(
                        title=_("This page without navigation"),
                        icon_name="frameurl",
                        item=PageMenuLink(Link(
                            url=html.makeuri([]),
                            target="_top",
                        )),
                    ),
                    PageMenuEntry(
                        title=_("This page with navigation"),
                        icon_name="pageurl",
                        item=PageMenuLink(
                            Link(
                                url=html.makeuri_contextless(
                                    [("start_url", html.makeuri([]))],
                                    filename="index.py",
                                ),
                                target="_top",
                            )),
                    ),
                ],
            ),
        ],
    )


def make_help_dropdown() -> PageMenuDropdown:
    return PageMenuDropdown(
        name="help",
        title=_("Help"),
        topics=[
            PageMenuTopic(
                title=_("Context sensitive help"),
                entries=[
                    PageMenuEntry(
                        title=_("Toggle inline help on this page"),
                        icon_name="help",
                        item=make_javascript_link("cmk.help.toggle()"),
                        name="inline_help",
                        is_enabled=False,
                    )
                ],
            ),
            PageMenuTopic(
                title=_("Articles in the user guide"),
                entries=[
                    PageMenuEntry(
                        title=_("Checkmk - The official guide"),
                        icon_name="manual",
                        item=make_external_link("https://checkmk.com/cms_index.html"),
                    ),
                ],
            ),
        ],
    )


class PageMenuRenderer:
    """Renders the given page menu to the page header"""
    def show(self, menu: PageMenu) -> None:
        html.open_table(id_="page_menu_bar", class_="menubar")

        html.open_tr()
        self._show_dropdowns(menu)
        self._show_shortcuts(menu)
        self._show_async_progress_msg_container()
        html.close_tr()

        self._show_suggestions(menu)
        html.close_table()

    def _show_dropdowns(self, menu: PageMenu) -> None:
        html.open_td(class_="menues")

        for dropdown in menu.dropdowns:
            if dropdown.is_empty:
                continue

            html.open_div(class_="menucontainer")

            self._show_dropdown_trigger(dropdown)
            self._show_dropdown_area(dropdown)

            html.close_div()  # menucontainer

        html.close_td()

    def _show_dropdown_trigger(self, dropdown: PageMenuDropdown) -> None:
        html.open_div(class_="menutitle",
                      onclick="cmk.page_menu.toggle(this)",
                      onmouseenter="cmk.page_menu.switch_menu(this)")
        html.h2(dropdown.title)
        html.close_div()

    def _show_dropdown_area(self, dropdown: PageMenuDropdown) -> None:
        id_ = id_ = "menu_%s" % dropdown.name
        show_more = html.foldable_container_is_open("more_buttons", id_, isopen=False)
        html.open_div(class_=["menu", ("more" if show_more else "less")], id_=id_)

        if dropdown.any_advanced_entries:
            html.open_div(class_=["more_container"])
            html.more_button(id_, dom_levels_up=2)
            html.close_div()

        for topic in dropdown.topics:
            self._show_topic(topic)

        html.close_div()

    def _show_topic(self, topic: PageMenuTopic) -> None:
        html.open_div(class_="topic")
        html.div(topic.title, class_="topic_title")

        for entry in topic.entries:
            self._show_entry(entry)

        html.close_div()

    def _show_entry(self, entry: PageMenuEntry) -> None:
        classes = [
            "entry",
            ("enabled" if entry.is_enabled else "disabled"),
            ("advanced" if entry.is_advanced else "basic"),
        ]

        html.open_div(class_=classes, id_="menu_entry_%s" % entry.name)

        #if self.disabled_reason:
        #    html.open_div(class_="tooltip")

        DropdownEntryRenderer().show(entry)

        #if self.disabled_reason:
        #    html.span(_("This action is currently not possible: ") + self.disabled_reason,
        #              class_="disabled tooltiptext")
        #    html.close_div()

        html.close_div()

    def _show_shortcuts(self, menu: PageMenu) -> None:
        html.open_td(class_="shortcuts")

        for entry in menu.shortcuts:
            ShortcutRenderer().show(entry)

        html.close_td()

    def _show_async_progress_msg_container(self) -> None:
        html.open_td(id_="async_progress_msg")
        html.show_message("")
        html.close_td()

    def _show_suggestions(self, menu: PageMenu) -> None:
        entries = menu.suggestions
        if not entries:
            return

        html.open_tr(id_="suggestions")
        html.open_td(colspan=3)
        for entry in entries:
            html.open_div(class_="suggestion")
            SuggestedEntryRenderer().show(entry)
            html.close_div()
        html.close_td()
        html.close_tr()


class SuggestedEntryRenderer:
    """Render the different item types for the suggestion area"""
    def show(self, entry: PageMenuEntry) -> None:
        if isinstance(entry.item, PageMenuLink):
            self._show_link_item(entry, entry.item)
        else:
            raise NotImplementedError("Suggestion rendering not implemented for %s" % entry.item)

    def _show_link_item(self, entry: PageMenuEntry, item: PageMenuLink):
        html.open_a(href=item.link.url, onclick=item.link.onclick)
        html.icon(title=None, icon=entry.icon_name or "trans")
        html.write_text(entry.title)
        html.close_a()


class ShortcutRenderer:
    """Render the different item types for the shortcut area"""
    def show(self, entry: PageMenuEntry) -> None:
        if isinstance(entry.item, PageMenuLink):
            self._show_link_item(entry, entry.item)
        else:
            raise NotImplementedError("Shortcut rendering not implemented for %s" % entry.item)

    def _show_link_item(self, entry: PageMenuEntry, item: PageMenuLink):
        classes = ["link", "enabled" if entry.is_enabled else "disabled"]
        if entry.is_suggested:
            classes.append("suggested")

        html.open_div(class_="tooltip")
        html.icon_button(url=item.link.url,
                         onclick=item.link.onclick,
                         title=entry.title,
                         icon=entry.icon_name,
                         target=item.link.target,
                         class_=" ".join(classes),
                         id_=("menu_shortcut_%s" % entry.name if entry.name else None))
        html.span(entry.title, class_="tooltiptext")
        html.close_div()


class DropdownEntryRenderer:
    """Render the different item types for the dropdown menu"""
    def show(self, entry: PageMenuEntry) -> None:
        if isinstance(entry.item, PageMenuLink):
            self._show_link_item(entry.title, entry.icon_name, entry.item)
        else:
            raise NotImplementedError("Rendering not implemented for %s" % entry.item)

    def _show_link_item(self, title: str, icon_name: str, item: PageMenuLink):
        html.icon(title=None, icon=icon_name or "trans")

        if item.link.url is not None:
            html.a(title, href=item.link.url, target=item.link.target)
        else:
            html.a(title, href="javascript:void(0)", onclick=item.link.onclick)
