#!/bin/bash

# Copyright (c) 2026 Robert Bosch GmbH and its subsidiaries.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# __author__      = "Min Hee Jo"
# __copyright__   = "Copyright 2026, Robert Bosch GmbH"
# __license__     = "AGPL"
# __version__     = "3.0"
# __email__       = "minhee.jo@de.bosch.com"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKING_DIR="$(dirname "$SCRIPT_DIR")"

### assumption: the json file is already created on the GPU

# convert json files to strace command options
python3 ${WORKING_DIR}/src/process_json/main.py
