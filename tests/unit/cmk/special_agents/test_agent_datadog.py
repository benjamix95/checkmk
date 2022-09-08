#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from http import HTTPStatus

import pytest
import requests
from pytest import MonkeyPatch

from cmk.special_agents import agent_datadog
from cmk.special_agents.agent_datadog import (
    _event_to_syslog_message,
    Event,
    EventsQuerier,
    MonitorsQuerier,
    parse_arguments,
)


def test_parse_arguments() -> None:
    parse_arguments(
        [
            "testhost",
            "12345",
            "powerg",
            "api.datadoghq.eu",
            "--monitor_tags",
            "t1",
            "t2",
            "--monitor_monitor_tags",
            "mt1",
            "mt2",
            "--event_max_age",
            "90",
            "--event_tags",
            "t3",
            "t4",
            "--event_tags_show",
            ".*",
            "--event_syslog_facility",
            "1",
            "--event_syslog_priority",
            "1",
            "--event_service_level",
            "0",
            "--event_add_text",
            "--sections",
            "monitors",
            "events",
        ]
    )


class MockDatadogAPI:
    def __init__(self, page_to_data: Mapping[object, object]) -> None:
        self.page_to_data = page_to_data

    def get_request(
        self,
        api_endpoint: str,
        params: Mapping[str, str | int],
        version: str = "v1",
    ) -> requests.Response:
        if (resp := self.page_to_data.get(params["page"])) is None:
            raise RuntimeError
        return self._response(HTTPStatus.OK, json_data=resp)

    @staticmethod
    def _response(status_code: HTTPStatus, json_data: object = None) -> requests.Response:
        response = requests.Response()
        response.status_code = int(status_code)
        if json_data is not None:
            response._content = json.dumps(json_data).encode()
        return response


class TestMonitorsQuerier:
    def test_query_monitors(
        self,
    ) -> None:
        # note: this data is of course incomplete, but sufficient for this test
        monitors_data = [
            {
                "name": "monitor1",
            },
            {
                "name": "monitor2",
            },
            {
                "name": "monitor3",
            },
        ]

        datadog_api = MockDatadogAPI(page_to_data={0: monitors_data, 1: []})

        assert (
            list(
                MonitorsQuerier(datadog_api).query_monitors(
                    [],
                    [],
                )
            )
            == monitors_data
        )


class TestEventsQuerier:
    @pytest.fixture(name="events")
    def fixture_events(self) -> list[Event]:
        return [
            Event(
                id=1,
                tags=[],
                text="text",
                date_happened=123456,
                host="host",
                title="event1",
                source="source",
            ),
            Event(
                id=2,
                tags=[],
                text="text",
                date_happened=123456,
                host="host",
                title="event2",
                source="source",
            ),
            Event(
                id=3,
                tags=[],
                text="text",
                date_happened=123456,
                host="host",
                title="event3",
                source="source",
            ),
        ]

    @pytest.fixture(name="datadog_api")
    def fixture_datadog_api(
        self,
        events: Sequence[Event],
    ) -> MockDatadogAPI:
        return MockDatadogAPI(
            page_to_data={
                0: {"events": [event.dict() for event in events]},
                1: {"events": []},
            }
        )

    @pytest.fixture(name="events_querier")
    def fixture_events_querier(self, datadog_api: MockDatadogAPI) -> EventsQuerier:
        return EventsQuerier(
            datadog_api,
            "host_name",
            300,
        )

    def test_events_query_time_range(
        self,
        monkeypatch: MonkeyPatch,
        events_querier: EventsQuerier,
    ) -> None:
        now = 1601310544
        monkeypatch.setattr(
            agent_datadog.time,
            "time",
            lambda: now,
        )
        assert events_querier._events_query_time_range() == (
            now - events_querier.max_age,
            now,
        )

    def test_query_events_no_previous_ids(
        self,
        events_querier: EventsQuerier,
        events: Sequence[Event],
    ) -> None:
        assert list(events_querier.query_events([])) == events
        assert events_querier.id_store.read() == frozenset({1, 2, 3})

    def test_query_events_with_previous_ids(
        self,
        events_querier: EventsQuerier,
        events: Sequence[Event],
    ) -> None:
        events_querier.id_store.write([1, 2, 5])
        assert list(events_querier.query_events([])) == events[-1:]
        assert events_querier.id_store.read() == frozenset({1, 2, 3})


def test_event_to_syslog_message() -> None:
    assert (
        repr(
            _event_to_syslog_message(
                Event(
                    id=5938350476538858876,
                    tags=[
                        "ship:enterprise",
                        "location:alpha_quadrant",
                        "priority_one",
                    ],
                    text="Abandon ship\n, abandon ship!",
                    date_happened=1618216122,
                    host="starbase 3",
                    title="something bad happened",
                    source="main bridge",
                ),
                [
                    "ship:.*",
                    "^priority_one$",
                ],
                1,
                1,
                0,
                True,
            )
        )
        == '<9>1 2021-04-12T08:28:42+00:00 - - - - [Checkmk@18662 host="starbase 3" application="main bridge"] something bad happened, Tags: ship:enterprise, priority_one, Text: Abandon ship ~ , abandon ship!'
    )
