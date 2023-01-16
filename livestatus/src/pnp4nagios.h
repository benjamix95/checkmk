// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#ifndef pnp4nagios_h
#define pnp4nagios_h

#include "config.h"  // IWYU pragma: keep

#include <string>
class MonitoringCore;
int pnpgraph_present(MonitoringCore *mc, const std::string &host,
                     const std::string &service);

#endif  // pnp4nagios_h
