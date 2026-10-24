"""One handler per trip operation, independent of routing and HTTP parsing."""
import database


class TripHandlers:
    def get_trips(self, trip_id):
        if trip_id is None:
            self.respond(200, database.list_trips(self.database_path))
            return
        self.respond_with_trip(database.get_trip(self.database_path, trip_id))

    def create_trip(self, _trip_id):
        trip = database.save_trip(self.database_path, self.read_payload())
        self.respond(201, trip)

    def update_trip(self, trip_id):
        trip = database.save_trip(self.database_path, self.read_payload(), trip_id)
        self.respond_with_trip(trip)

    def delete_trip(self, trip_id):
        if not database.delete_trip(self.database_path, trip_id):
            self.respond(404, {'error': 'Trip not found.'})
            return
        self.respond(200, {'deleted': True})

    def respond_with_trip(self, trip):
        if trip is None:
            self.respond(404, {'error': 'Trip not found.'})
            return
        self.respond(200, trip)
