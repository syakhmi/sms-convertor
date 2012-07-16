sms-convertor
=============

Reads in SMS messages from various database and backup formats and outputs them in SMS Backup &amp; Restore's XML format.

License
-------

>This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

>This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

>You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Dependencies
------------

Requires <code>pyquery</code> and <code>sqlite3</code> python modules.

Usage
-----

<pre><code>sms_convertor -[SMS source type] [filename] -[SMS source type] [filename] ... [output filename]</code></pre>
	where [SMS source type] may be iphone, android, or webos

Example:
<pre><code>sms_convertor -iphone 3d0d7e5fb2ce288813306e4d4636395e047a3d28 -webos PalmDatabase.db3
 	-android backup.xml output.xml</code></pre>

This script can accept any number of input files:
<ul>
	<li>-iphone: iPhone SMS/iMessage sqlite files (for instructions on how to retrieve this, look online)
	<li>-webos: PalmDatabase.db3 files from WebOS (for instructions on how to retrieve this, look online)
	<li>-android: XML files produced by SMS Backup &amp; Restore for Android (by Ritesh Sahu)
</ul>

Output is written in the same XML format used by SMS Backup &amp; Restore