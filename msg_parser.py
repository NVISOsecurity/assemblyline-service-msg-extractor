import extract_msg
import json, os, re
from natsort import natsorted

from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.result import Result, ResultSection, BODY_FORMAT

class MsgParser(ServiceBase):
	def __init__(self, config=None):
		super(MsgParser, self).__init__(config)

	def start(self):
		self.log.debug("Msg parser service started")

	def stop(self):
		self.log.debug("Msg parser service ended")

	def execute(self, request):
		result = Result()
		file = request.file_path

		try:
			msg = extract_msg.openMsg(file)

			# Handling the header
			header = dict(natsorted(msg.header.items()))
			kv_section = ResultSection("Email Headers", body_format=BODY_FORMAT.KEY_VALUE, body=json.dumps(header))

			# Basic tags
			kv_section.add_tag("network.email.address", header["From"].strip())
			for to in header["To"].split(","):
				kv_section.add_tag("network.email.address", to.strip())
			kv_section.add_tag("network.email.date", header["Date"].strip())
			kv_section.add_tag("network.email.subject", header["Subject"].strip())

			# Add Message ID to body and tags
			if "Message-ID" in header:
				kv_section.add_tag("network.email.msg_id", header["Message-ID"][1:-1].strip())

			# Add Tags for received IPs
			if "Received" in header:
				ips = re.findall("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", header["Received"])
				for ip in ips:
					kv_section.add_tag("network.static.ip", ip.strip())
			if "X-Sender-IP" in header:
				kv_section.add_tag("network.static.ip", header["X-Sender-IP"].strip())

			# Add Tags for received Domains
			if "X-ClientProxiedBy" in header:
				for dom in header["X-ClientProxiedBy"].split("To"):
					kv_section.add_tag("network.static.domain", re.sub("\(.*\)", "", dom).strip().lower())
			if "X-MS-Exchange-CrossTenant-AuthSource" in header:
				kv_section.add_tag("network.static.domain", header["X-MS-Exchange-CrossTenant-AuthSource"].lower())

			# Handling the attachments
			msg.save_attachments(customPath=self.working_directory)
			for ofile in os.listdir(self.working_directory):
				request.add_extracted(self.working_directory + "/" + ofile, ofile, "Attachment")

			result.add_section(kv_section)
		except OSError:
			text_section = ResultSection("Failed to analyze")
			result.add_section(text_section)

		request.result = result
