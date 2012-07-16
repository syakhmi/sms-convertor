#!/usr/bin/python
# coding: UTF-8
# version: 2.7

# Copyright (c) 2012 Sahil Yakhmi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# USAGE: sms_convertor.py -[SMS source type] [filename] -[SMS source type] [filename] ... [output filename]
# 			where [SMS source type] may be iphone, android, or webos
# 
# EXAMPLE: sms_convertor.py -iphone 3d0d7e5fb2ce288813306e4d4636395e047a3d28 -webos PalmDatabase.db3
#  			-android backup.xml output.xml
# 
# This script can accept any number of input files:
# 	-iphone: iPhone SMS/iMessage sqlite files (for instructions on how to retrieve this, look online)
# 	-webos: PalmDatabase.db3 files from WebOS (for instructions on how to retrieve this, look online)
# 	-android: XML files produced by SMS Backup & Restore for Android (by Ritesh Sahu)
# 
# Output is written in the same XML format used by SMS Backup & Restore

from pyquery import PyQuery as pq
import re
import codecs
import sqlite3
import cgi
import sys
from htmlentitydefs import codepoint2name
from datetime import datetime
from datetime import timedelta

ARGS = sys.argv[1:]

IPHONE_SELECT = 'select * from message'
WEBOS_SELECT = 'select com_palm_pim_Recipient.address, com_palm_pim_FolderEntry.smsClass, \
com_palm_pim_Recipient.firstName, com_palm_pim_Recipient.lastName, \
com_palm_pim_FolderEntry.fromAddress, com_palm_pim_FolderEntry.timeStamp, \
com_palm_pim_FolderEntry.messageText from com_palm_pim_FolderEntry \
join com_palm_pim_Recipient on (com_palm_pim_FolderEntry.id = \
com_palm_pim_Recipient.com_palm_pim_FolderEntry_id) \
where messageType="SMS" order by timeStamp;'
MADRID_OFFSET = 978307200 #iMessage timestamps count seconds since 1 Jan 2001

def ParseMillis(millis):
	time = str(millis)
	d = datetime.fromtimestamp(millis/1000)
	d = d + timedelta(microseconds=int(time[-3:])*1000)
	return d

def sms_compare(x, y):
	return int(long(x.date.strftime('%s%f')) - long(y.date.strftime('%s%f')))

class SMS:
	def __init__(self, address, millis, millis_sent, msg_type, text, status='-1'):
		self.address = address
		self.date = ParseMillis(millis)
		if millis_sent:
			self.date_sent = ParseMillis(millis_sent)
		else:
			self.date_sent = 0
		self.type = msg_type
		self.text = text
		self.status = status
	
	def ToXML(self, d):
		sms = d('<sms/>').attr('protocol', '0').attr('subject', 'null').attr('toa', 'null').attr('sc_toa', 'null').attr('service_center', 'null').attr('read', '1').attr('status', self.status).attr('locked', '0')
		sms.attr('date', self.date.strftime('%s%f')[:-3])
		sms.attr('address', self.address)
		sms.attr('readable_date', self.date.strftime("%b %e, %Y %l:%M:%S %p").replace('  ', ' '))
		if self.date_sent:
			sms.attr('date_sent', self.date_sent.strftime('%s%f')[:-3])
		else:
			sms.attr('date_sent', '0')
		sms.attr('type', str(self.type))
		sms.attr('body', self.text)
		return sms


#########################################
#             BEGIN PROGRAM             #
#########################################

curr_flag = ''
output_file = ''
android = []
iphone = []
webos = []
for arg in ARGS:
	if arg[:1] == '-':
		curr_flag = arg
	else:
		if curr_flag == '-android':
			android.append(arg)
		elif curr_flag == '-iphone':
			iphone.append(arg)
		elif curr_flag == '-webos':
			webos.append(arg)
		elif curr_flag:
			print 'Unrecognized flag: ' + arg
			sys.exit(1)
		else:
			if not output_file:
				output_file = arg
			else:
				print 'Extra argument: ' + arg
				sys.exit(1)
		curr_flag = ''

smss = []

# Iterate through each Android SMSBackupAndRestore-formatted XML
# file and append sms messages.
for file_name in android:
	f = open(file_name, 'r')
	d = pq(f.read())
	def add_sms_element(i, e):
		e = d(e)
		sms = SMS(e.attr('address'), long(e.attr('date')), long(e.attr('date_sent')), int(e.attr('type')), e.attr('body'), e.attr('status'))
		smss.append(sms)

	posts = d('sms')
	posts.each(add_sms_element)
	f.close()

# Iterate through each iPhone SMS/iMessage database
# file and append sms messages.
for file_name in iphone:
	conn = sqlite3.connect(file_name)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	for row in c.execute(IPHONE_SELECT).fetchall():
		if row['text']:
			sms_type = -1
			flags = int(row['flags'])
			date = long(row['date'])
			address = re.sub(r'[\s\-\(\)]', '', str(row['address']))
			if flags == 2:
				sms_type = 1
			elif flags == 3:
				sms_type = 2
			elif flags == 0:
				madrid_flags = int(row['madrid_flags'])
				if madrid_flags == 12289:
					sms_type = 1
				elif madrid_flags == 36869 or madrid_flags == 45061:
					sms_type = 2
			if row['is_madrid']:
				date = date + MADRID_OFFSET
				address = row['madrid_handle']
			sms = SMS(address, date*1000, 0, sms_type, row['text'])
			smss.append(sms)
	conn.close()

# Iterate through each PalmDatabase.db3
# file and append sms messages.
for file_name in webos:
	conn = sqlite3.connect(file_name)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	for row in c.execute(WEBOS_SELECT).fetchall():
		if row['messageText']:
			sms_type = '-1'
			if row['smsClass'] == 2:
				sms_type = 1
			elif row['smsClass'] == 0:
				sms_type = 2
			address = re.sub(r'[\s\-\(\)]', '', str(row['address']))
			sms = SMS(address, row['timeStamp'], 0, sms_type, row['messageText'])
			smss.append(sms)
	conn.close()

#order sms messages by timestamp
smss.sort(cmp=sms_compare)

#Generate new document tree with sms messages
smses = d('<smses/>').attr('count', str(len(smss)))
for sms in smss:
	smses.append(sms.ToXML(d))

#Write serialized XML file
f = codecs.open(output_file, 'w', 'utf-8')
f.write(smses.outerHtml().encode('ascii', 'xmlcharrefreplace'))
f.close()