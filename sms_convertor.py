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
# USAGE: sms_convertor.py -[source type flag] [filename] -[source type flag] [filename] ... [output filename]
# 			where [source type flag] may be iphone, db3, db8, or android
# 
# EXAMPLE: sms_convertor.py -iphone 3d0d7e5fb2ce288813306e4d4636395e047a3d28 -pdb3 PalmDatabase.db3
#  			-android backup.xml -db8 response.json output.xml
# 
# This script can accept any number of input files:
# 	-iphone: iPhone SMS/iMessage sqlite files (for instructions on how to retrieve this, look online)
# 	-pdb3: PalmDatabase.db3 files from WebOS 1.x (for instructions on how to retrieve this, look online)
#	-pdb8: db8 database service responses from WebOS 2.x + (_kind : com.palm.smsmessage:1)
# 	-android: XML files produced by SMS Backup & Restore for Android (by Ritesh Sahu)
# 
# Output is written in the same XML format used by SMS Backup & Restore

import codecs
import cgi
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from datetime import timedelta
from htmlentitydefs import codepoint2name
from pyquery import PyQuery as pq

FLAGS = ['-android', '-iphone', '-pdb3', '-pdb8']
IPHONE_SELECT = 'select * from message'
PDB3_SELECT = 'select com_palm_pim_Recipient.address, com_palm_pim_FolderEntry.smsClass, \
com_palm_pim_Recipient.firstName, com_palm_pim_Recipient.lastName, \
com_palm_pim_FolderEntry.fromAddress, com_palm_pim_FolderEntry.timeStamp, \
com_palm_pim_FolderEntry.messageText from com_palm_pim_FolderEntry \
join com_palm_pim_Recipient on (com_palm_pim_FolderEntry.id = \
com_palm_pim_Recipient.com_palm_pim_FolderEntry_id) \
where messageType="SMS" order by timeStamp;'
MADRID_OFFSET = 978307200 #iMessage timestamps count seconds since 1 Jan 2001
PHONE_CLEAN_REGEX = re.compile(r'[\s\-\(\)]+')

#A (hacky) way to make a datetime object from milliseconds since UNIX epoch
def ParseMillis(millis):
	time = str(millis)
	d = datetime.fromtimestamp(millis/1000)
	d = d + timedelta(microseconds=int(time[-3:])*1000)
	return d

class SMS:
	def __init__(self, address, millis, millis_sent, msg_type, text, status='-1'):
		self.address = address
		self.millis = millis
		self.date = ParseMillis(millis) #needed for readable_date
		if millis_sent:
			self.date_sent = ParseMillis(millis_sent)
		else:
			self.date_sent = 0
		self.type = msg_type
		self.text = text
		self.status = status
	
	def ToXMLNode(self, d):
		sms = d('<sms/>').attr('protocol', '0').attr('subject', 'null') \
			.attr('toa', 'null').attr('sc_toa', 'null').attr('service_center', 'null') \
			.attr('read', '1').attr('status', self.status).attr('locked', '0')
		sms.attr('date', str(self.millis))
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

def main(args):
	curr_flag = ''
	output_file = ''
	android = []
	iphone = []
	pdb3 = []
	pdb8 = []
	file_lists = [android, iphone, pdb3, pdb8]
	for arg in args:
		if arg[:1] == '-': #if argument is a flag
			if curr_flag: #if previous argument was also flag
				print >> sys.stderr, 'No filename specified for flag: ' + curr_flag
				sys.exit(1)
			if arg in FLAGS: #if argument is valid flag
				curr_flag = arg
			else:
				print >> sys.stderr, 'Unrecognized flag: ' + arg
				sys.exit(1)
		elif curr_flag: #if previous argument was a valid flag
			if not os.path.exists(arg): #if argument is not a valid file path
				print >> sys.stderr, 'File not found: ' + arg
				sys.exit(1)
			#append file path to correct file list
			file_lists[FLAGS.index(curr_flag)].append(arg)
			curr_flag = '' #reset to indicate in next iteration that prev arg was not a flag
		else: #if argument is not a flag and previous argument was not a flag
			if output_file: #if output file is already specified
				print >> sys.stderr, 'Extra argument: ' + arg
				sys.exit(1)
			output_file = arg
	if curr_flag: #if last argument was a valid flag
		print >> sys.stderr, 'No filename specified for flag: ' + curr_flag
		sys.exit(1)
	if not output_file: #if not output file specified
		print >> sys.stderr, 'No output file specified'
		sys.exit(1)

	smss = []

	# Iterate through each Android SMSBackupAndRestore-formatted XML
	# file and append sms messages.
	for file_name in android:
		f = open(file_name, 'r')
		d = pq(f.read())
		def add_sms_element(i, e):
			e = d(e)
			sms = SMS(e.attr('address'), long(e.attr('date')), long(e.attr('date_sent')), \
				int(e.attr('type')), e.attr('body'), e.attr('status'))
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
				address = PHONE_CLEAN_REGEX.sub('', str(row['address']))
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
	for file_name in pdb3:
		conn = sqlite3.connect(file_name)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		for row in c.execute(PDB3_SELECT).fetchall():
			if row['messageText']:
				sms_type = '-1'
				if row['smsClass'] == 2:
					sms_type = 1
				elif row['smsClass'] == 0:
					sms_type = 2
				address = PHONE_CLEAN_REGEX.sub('', str(row['address']))
				sms = SMS(address, row['timeStamp'], 0, sms_type, row['messageText'])
				smss.append(sms)
		conn.close()
	
	# Iterate through each db8 query result
	# file and append sms messages.
	for file_name in pdb8:
		f = open(file_name, 'r')
		response = json.loads(f.read())
		for message in response['results']:
			if message['status'] == 'successful' and message['messageText']:
				if 'from' in message: #received
					sms_type = 1
					address = PHONE_CLEAN_REGEX.sub('', message['from']['addr'])
				elif 'to' in message: #sent
					sms_type = 2
					to_list = message['to']
					address = PHONE_CLEAN_REGEX.sub('', to_list[0]['addr'])
				else: #problem with message
					continue
				sms = SMS(address, message['localTimestamp'], message['timestamp']*1000, sms_type, message['messageText'])
				smss.append(sms)
		f.close()

	#order sms messages by timestamp
	smss.sort(cmp=lambda x, y: int(x.millis - y.millis))

	#Generate new document tree with sms messages
	smses = pq('<smses/>').attr('count', str(len(smss)))
	for sms in smss:
		smses.append(sms.ToXMLNode(pq))

	#Write serialized XML file
	f = codecs.open(output_file, 'w', 'utf-8')
	xml = smses.outerHtml() #serialize
	xml = xml.encode('ascii', 'xmlcharrefreplace').replace('\n', '&#10;') #escape chars
	f.write(xml)
	f.close()

if __name__ == '__main__':
    main(sys.argv[1:])