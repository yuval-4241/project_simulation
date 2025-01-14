
     def __init__(self,time):
        super().__init__(time)
        self.guestGroup=GuestGroup(self.time) #self.time=ariive time of the guest group to the hotel

     def handle(self,simulation):
        if simulation.hotel.checkFreeRooms(self.guestGroup) and simulation.hotel.openToPublicStatus: #there is a room for the group and the hotel is open to public, the room is booked for them
            simulation.hotel.calculateLambda()
            availableServer = simulation.hotel.findAvailableServer()
            if availableServer is not None: # there is an available server in the desk
                availableServer.changeWorkingStatus(True)
                serviceTime = sampleServiceCheckIn()
                simulation.scheduleEvent(FinishCheckInEvent(self.time, serviceTime, availableServer, self.guestGroup))# Assign customer to available server
            else: # there is non available server in the desk
                simulation.hotel.checkInOutQueue.append(self.guestGroup) # Add customer to the common queue
        # Schedule the next arrival
        nextArrivalTime = self.time + sampleNextArrivelTime(simulation.hotel.getLambda()) #*********************************************** need to calc lambda val
        if nextArrivalTime < simulation.simulationTime:
            simulation.scheduleEvent(StartCheckInEvent(nextArrivalTime))
