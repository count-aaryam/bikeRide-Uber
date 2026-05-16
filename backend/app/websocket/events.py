# Centralised event definitions
# Every WebSocket message in the app uses these event names

class RideEvents:
    NEW_RIDE_REQUESTED      = "new_ride_requested"
    RIDE_ACCEPTED           = "ride_accepted"
    DRIVER_ARRIVING         = "driver_arriving"
    RIDE_STARTED            = "ride_started"
    RIDE_COMPLETED          = "ride_completed"
    RIDE_CANCELLED          = "ride_cancelled"
    DRIVER_LOCATION_UPDATED = "driver_location_updated"
    ERROR                   = "error"