from google.appengine.ext import ndb

import webapp2
import json
import ndb_json

class Boat(ndb.Model):
	name = ndb.StringProperty(required=True)
	type = ndb.StringProperty(required=True)
	length = ndb.IntegerProperty(required=True)
	at_sea = ndb.BooleanProperty()

class Slip(ndb.Model):
	id = ndb.StringProperty()
	number = ndb.IntegerProperty()
	current_boat = ndb.StringProperty()
	arrival_date = ndb.StringProperty()
	departure_history = ndb.JsonProperty()
	
class BoatHandler(webapp2.RequestHandler):
	# Get all boats
	def get(self):
		query = Boat.query()
		allEntities = query.fetch()
		query_json = ndb_json.dumps(allEntities)
		query_dict = ndb_json.loads(query_json)
		
		for i in range(0, Boat.query().count()):
			query_dict[i]['id'] = allEntities[i].key.urlsafe()
			
		output = json.dumps(query_dict)
		self.response.write(output)
		self.response.headers['Content-Type'] = 'application/json'
	
	# Boat Creation
	def post(self):
		try:
			boat_data = json.loads(self.request.body)
			
			if ('name' in boat_data and \
				'type' in boat_data and \
				'length' in boat_data):
				
				new_boat = Boat(
					name=boat_data['name'],
					type=boat_data['type'],
					length=boat_data['length'],
					at_sea=True
				)
				new_boat.put()
				boat_dict = new_boat.to_dict()
				boat_dict['id'] = new_boat.key.urlsafe()
				self.response.status = 201
				self.response.write(json.dumps(boat_dict))
				self.response.headers['Content-Type'] = 'application/json'
				
			else:
				self.response.status = 400
			
		except:
			self.response.status = 400

class SlipHandler(webapp2.RequestHandler):
	def get(self):
		query = Slip.query()
		allEntities = query.fetch()
		query_json = ndb_json.dumps(query)
		query_dict = ndb_json.loads(query_json)
		
		for i in range(0, Slip.query().count()):
			query_dict[i]['id'] = allEntities[i].key.urlsafe()
			
		output = json.dumps(query_dict)
		self.response.write(output)
		self.response.headers['Content-Type'] = 'application/json'
	
	def post(self):
		try:
			slip_data = json.loads(self.request.body)
			
			# Check if this slip number has already been used
			slipByNum = Slip.query(Slip.number == slip_data.get('number')).get()
			if slipByNum == None:
				
				if ('number' in slip_data):
					
					new_slip = Slip(number=slip_data['number'])
					new_slip.put()
					slip_dict = new_slip.to_dict()
					slip_dict['id'] = new_slip.key.urlsafe()
					self.response.status = 201
					self.response.write(json.dumps(slip_dict))
					self.response.headers['Content-Type'] = 'application/json'
					
				else:
					self.response.status = 400
			
			else:
				self.response.status = 403
			
		except:
			self.response.status = 400
		
class BoatIdHandler(webapp2.RequestHandler):
	def get(self, id=None):
		try:
			key = ndb.Key(urlsafe=id)
			b = Boat.get_by_id(key.id())
		
		except:
			self.response.status = 404
			return
			
		try:
			b_d = b.to_dict()
			b_d['id'] = id
			self.response.write(json.dumps(b_d))
			self.response.headers['Content-Type'] = 'application/json'
								
		except:
			self.response.status = 400
	
	
	def patch(self, id=None):
		try:
			body = self.request.body
			data = json.loads(body)
			
			# Get initial values
			key = ndb.Key(urlsafe=id)
			b = Boat.get_by_id(key.id())
			
			if data.get('name'):
				b.name = data.get('name')
			if data.get('type'):
				b.type = data.get('type')
			if data.get('length'):
				b.length = data.get('length')
				
			b.put()
			self.response.status = 204
			
		except:
			self.response.status = 400
	
	def put(self, id=None):
		try:
			body = self.request.body
			data = json.loads(body)
			
			# Get initial values
			key = ndb.Key(urlsafe=id)
			b = Boat.get_by_id(key.id())
			
			if not (data.get('name') or \
					data.get('type') or \
					data.get('length')):
				self.response.status = 400
			else:
				b.name = data.get('name')
				b.type = data.get('type')
				b.length = data.get('length')
								
			b.put()
			self.response.status = 204
			
		except:
			self.response.status = 400
	
	def delete(self, boatId=None):
		try:
			boatKey = ndb.Key(urlsafe=boatId)
			boat = Boat.get_by_id(boatKey.id())
			
			if not boat:
				self.response.status = 400
			
			else:
				slip = Slip.query(Slip.current_boat == boatId).get()
				
				if slip:
					if not slip.departure_history:
						slip.departure_history = []
					new_dept = {'departure_date': None, 'departed_boat': boatId}
					slip.departure_history.append(new_dept)
					
					slip.arrival_date = None
					slip.current_boat = None
					slip.put()
				
				boat.key.delete()
				self.response.status = 204
		
		except:
			self.response.status = 400

			
class SlipIdHandler(webapp2.RequestHandler):
	def get(self, id=None):
			try:
				key = ndb.Key(urlsafe=id)
				slip = Slip.get_by_id(key.id())
			
			except:
				self.response.status = 404
				return
				
			try:
				slip_dict = slip.to_dict()
				slip_dict['id'] = id
				self.response.write(json.dumps(slip_dict))
				self.response.headers['Content-Type'] = 'application/json'
			except:
				self.response.status = 400
	
	
	def patch(self, id=None):
		try:
			body = self.request.body
			data = json.loads(body)
			
			# Get initial values
			key = ndb.Key(urlsafe=id)
			slip = Slip.get_by_id(key.id())
			
			if data.get('number'):
				slip.number = data.get('number')
			
			if (data.get('arrival_date') and \
				slip.current_boat != None):
				slip.arrival_date = data.get('arrival_date')
			
			# Check if this number is already being used
			slipByNum = None
			if data.get('number'):
				slipByNum = Slip.query(Slip.number == data.get('number')).get()
				
			if slipByNum != None:
				self.response.status = 403
			
			else:
				slip.put()
				self.response.status = 204
				
		except:
			self.response.status = 400
	
	def put(self, id=None):
		try:
			body = self.request.body
			data = json.loads(body)
			
			# Get initial values
			key = ndb.Key(urlsafe=id)
			slip = Slip.get_by_id(key.id())
			
			if not (data.get('number')):
				self.response.status = 400
				
			else:
				# Check if the number is already in use
				slipByNum = Slip.query(Slip.number == data.get('number')).get()
				
				if slipByNum == None:
					slip.number = data.get('number')
					slip.arrival_date = data.get('arrival_date')
					slip.departure_history = None 
					
					slip.put()
					self.response.status = 204
				else:
					self.response.status = 400
					
		except:
			self.response.status = 400
	
	def delete(self, slipId=None):
		try:
			slipKey = ndb.Key(urlsafe=slipId)
			slip = Slip.get_by_id(slipKey.id())
			
			# Check if there is a current boat to release from the slip
			if slip.current_boat:
				boatKey = ndb.Key(urlsafe=slip.current_boat)
				boat = Boat.get_by_id(boatKey.id())
				
				boat.at_sea = True
				boat.put()
				
			slip.key.delete()
			self.response.status = 204
		
		except:
			self.response.status = 400

			
class ArrivalHandler(webapp2.RequestHandler):
	def put(self, slipId=None, boatId=None):
		try:
			body = self.request.body
			data = json.loads(body)
			
			# Get initial values
			slipKey = ndb.Key(urlsafe=slipId)
			slip = Slip.get_by_id(slipKey.id())
			boatKey = ndb.Key(urlsafe=boatId)
			boat = Boat.get_by_id(boatKey.id())
			
			# First check if there is already a boat at this slip
			if (slip.current_boat == None and \
				boat.at_sea == True and \
				data.get('arrival_date')):
				
				slip.current_boat = boatId
				slip.arrival_date = data.get('arrival_date')
				boat.at_sea = False
				slip.put()
				boat.put()
				self.response.status = 204
				
			else:
				self.response.status = 403
		
		except:
			self.response.status = 400
	

class DepartHandler(webapp2.RequestHandler):
	def put(self, boatId=None):
		try:
			body = self.request.body
			data = json.loads(body)
			
			boatKey = ndb.Key(urlsafe=boatId)
			boat = Boat.get_by_id(boatKey.id())
			
			if boat.at_sea == True:
				self.response.status = 403
			
			else:
				if data.get('departure_date'):
					
					if isinstance(data.get('departure_date'), basestring):
						boat.at_sea = True			
						slip = Slip.query(Slip.current_boat == boatId).get()
						slip.arrival_date = None
						slip.current_boat = None
						
						if not slip.departure_history:
							slip.departure_history = []
						new_dept = {'departure_date': data.get('departure_date'), 'departed_boat': boatId}
						slip.departure_history.append(new_dept)
						
						boat.put()
						slip.put()
						self.response.status = 204
					
					else:
						self.response.status = 400
				
				else:
					self.response.status = 400
					
		except:
			self.response.status = 400
	

class LookupBoatHandler(webapp2.RequestHandler):
	def get(self, slipId=None):
		try:
			slipKey = ndb.Key(urlsafe=slipId)
			slip = Slip.get_by_id(slipKey.id())
			
			if slip.current_boat != None:
				
				boatKey = ndb.Key(urlsafe=slip.current_boat)
				boat = Boat.get_by_id(boatKey.id())
				boat_dict = boat.to_dict()
				boat_dict['id'] = slip.current_boat
				self.response.write(json.dumps(boat_dict))
				self.response.headers['Content-Type'] = 'application/json'
			
			else:
				self.response.status = 404
		
		except:
			self.response.status = 400

class LookupSlipHandler(webapp2.RequestHandler):
	def get(self, boatId=None):
		try:
			if boatId:
				slip = Slip.query(Slip.current_boat == boatId).get()
				
				if slip != None:
					slip_json = ndb_json.dumps(slip)
					slip_dict = ndb_json.loads(slip_json)
					
					slipKey = slip.key
					slip_dict['id'] = slipKey.urlsafe()
					
					self.response.write(json.dumps(slip_dict))
					self.response.headers['Content-Type'] = 'application/json'
				
				else:
					boatKey = ndb.Key(urlsafe=boatId)
					boat = Boat.get_by_id(boatKey.id())
					if boat:
						self.response.status = 404
					else:
						self.response.status = 400
			
			else:
				self.response.status = 400
		
		except:
			self.response.status = 400
			

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("welcome!")
		
	
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
	('/slip/(.*)/boat', LookupBoatHandler),
	('/boat/(.*)/slip', LookupSlipHandler),
	('/boats', BoatHandler),
	('/boats/(.*)/depart', DepartHandler),
	('/boats/(.*)', BoatIdHandler),
	('/slip/(.*)/boat/(.*)', ArrivalHandler),
	('/slips', SlipHandler),
	('/slips/(.*)', SlipIdHandler),
	
], debug=True)