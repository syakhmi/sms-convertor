sms-convertor
=============

Reads in SMS messages from various database and backup formats and outputs them in the XML format used by Ritesh Sahu's <a href="https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore">SMS Backup &amp; Restore</a>. This script can be used to help transfer old text messages (currently from iOS and WebOS devices) to an Android phone, but can also be used as a starting point for an archival tool.

License
-------

Copyright &copy; 2012 Sahil Yakhmi

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

<pre><code>sms_convertor.py -[source type flag] [filename] -[source type flag] [filename] ... [output filename]</code></pre>

where <code>[source type flag]</code> may be <code>iphone</code>, <code>db3</code>, <code>db8</code>, or <code>android</code>

Example:
<pre><code>sms_convertor.py -iphone 3d0d7e5fb2ce288813306e4d4636395e047a3d28 -db3 PalmDatabase.db3
 	-db8 response.json -android backup.xml output.xml</code></pre>

This script can accept any number of input files:
<ul>
	<li><code>-iphone</code>: iPhone SMS/iMessage sqlite files (for instructions on how to retrieve this, look online)
	<li><code>-db3</code>: PalmDatabase.db3 files from WebOS 1.x (for instructions on how to retrieve this, look online)
	<li><code>-db8</code>: db8 database service responses from WebOS 2.x + (_kind : com.palm.smsmessage:1)
	<li><code>-android</code>: XML files produced by SMS Backup &amp; Restore for Android
</ul>

Output is written in the same XML format used by SMS Backup &amp; Restore
