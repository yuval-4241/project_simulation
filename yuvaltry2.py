from samples import *
from events import *


class Room:
    totalRooms = 0  # Static variable to track the total number of rooms created

    def __init__(self, roomType):
        """
        Initialize a Room instance.
        :param roomType: Type of the room (e.g., Suite, Family).
        """
        Room.totalRooms += 1
        self.roomId = Room.totalRooms
        self.roomType = roomType
        self.currentBooking = None  # The guest group currently occupying the room
        self.available = True  # Indicates if the room is free


    def isAvailable(self):
        """
        Check if the room is free.
        :return: True if the room is not occupied, False otherwise.
        """
        return self.available

    def bookRoom(self, booking):
        """
        Assign a guest group to the room and mark it as occupied.
        :param guestGroup: The guest group to assign to the room.
        """
        self.currentBooking = booking
        self.available = False

    def getCurrentBooking(self):
        """
        Return the current guest group occupying the room.
        :return: The current booking (guest group) or None if the room is unoccupied.
        """
        return self.currentBooking

    def change_to_available_room(self):

        """
        מסמן את החדר כפנוי ומשחרר את ההזמנה הנוכחית.
        """
        if self.currentBooking:  # אם יש הזמנה פעילה
            ##print(f"Room of type {self.roomType} is now free.")
            self.currentBooking = None  # שחרור ההזמנה
            self.available = True  # סימון החדר כפנוי
        #else:
            ##print(f"Room of type {self.roomType} is already free.")


class Table:
    """
    מחלקה המייצגת שולחן במסעדת המלון
    """
    def __init__(self):
        self.is_occupied = False  # האם השולחן תפוס

    def set_status(self, status):
        """
        שינוי סטטוס השולחן
        :param status: True אם תפוס, False אם פנוי
        """
        self.is_occupied = status

class Customer:
    countCustomers = 0

    def __init__(self, groupType, groupId):
        Customer.countCustomers += 1
        self.customerId = Customer.countCustomers
        self.groupId = groupId
        self.expenses = 0
        self.rank = 10
        self.groupType = groupType
        self.currentDay = 1
        self.last_activity=None
        self.daily_activities, self.maxWaitingTime = self.initializeGroupAttributes()

    def initializeGroupAttributes(self):
        groupSettings = {
            "family": ({"pool": [False, 0], "bar": [False, 0]}, 10),
            "couple": ({"spa": [False, 0], "pool": [False, 0]}, 15),
            "individual": ({"spa": [False, 0], "bar": [False, 0], "pool": [False, 0]}, 20)
        }
        return groupSettings.get(self.groupType, ({}, 0))

    def update_rank(self, rank_decrease):
        self.rank = max(self.rank - rank_decrease, 0)

    def add_expense(self, expense):
        self.expenses += expense

    def get_expenses(self):
        return self.expenses

    def hasToDoActivity(self, activity_type):
        activity = self.daily_activities.get(activity_type)
        return activity and not activity[0] and activity[1] < 2

    def maxWaitingTimeInQ(self):
        return self.maxWaitingTime

    def checkGroupType(self):
        return self.groupType

    def updateRankExitLongQ(self):
        self.update_rank(0.03)

    def updateBarExpenses(self):
        drink_expenses = {
            "family" : [3],
            "couple": [3, 10, 15],
            "individual": [3, 10, 15]
        }

        food_expenses = {
            "family": [10, 12, 3, 15],
            "couple": [10, 12, 3, 15],
            "individual": [10, 12, 3, 15]
        }

        u1, u2 = np.random.uniform(), np.random.uniform()
        if u1 < 0.5:  # Drinks
            self.add_expense(self.choose_expense(drink_expenses[self.groupType], u2))
        else:  # Food
            self.add_expense(self.choose_expense(food_expenses[self.groupType], u2))

    def choose_expense(self, expense_options, probability):
        num_options = len(expense_options)
        for i in range(num_options):
            if probability < (i + 1) / num_options:
                return expense_options[i]
        return expense_options[-1]

    def __str__(self):
        return (f"Customer ID: {self.customerID}, Group ID: {self.groupId}, Group Type: {self.groupType}, "
                f"Rank: {self.rank}, Expenses: {self.expenses}")


class Booking:
    totalBookings = 0  # Static variable to track the total number of bookings

    def __init__(self, arrivalTime):
        """
        Initialize a new booking with group details and activities.
        """
        Booking.totalBookings += 1
        self.bookingId = Booking.totalBookings
        self.customers = []  # Changed to lowercase for consistency
        self.numCustomers = sampleCustomerCount()
        self.stayDuration = sampleStayDuration()
        self.arrivalTime = arrivalTime
        self.groupType = self.checkGroupType()
        self.breakfastArrivalTime = 0
        self.hasCheckedOut = False
        for i in range(self.numCustomers):
            self.customers.append(Customer(self.groupType, self.bookingId))

        # Create customers based on the group category

    def __lt__(self, other):
        """
        השוואה בין הזמנות על בסיס זמן הגעה.
        """
        return self.arrivalTime < other.arrivalTime

    def resetDailyActivities(self):
        """
        מאפסת את יומן הפעילויות של כל לקוח בהזמנה.
        """
        for customer in self.customers:
            customer.lastActivity = None
            customer.daily_activities, customer.maxWaitingTime = customer.initializeGroupAttributes()



    def getGroupSize(self):
        """
        Return the size of the group.
        """
        return self.numCustomers

    def getDurationtime(self):
        return self.stayDuration
    def checkGroupType(self):
        """
        Categorize the group based on its size.
        """
        if self.numCustomers >= 3:
            return "family"
        elif self.numCustomers == 2:
            return "couple"
        return "individual"


    def isLastDay(self, currentTime):
        """
            Check if it's the last day of the group's stay.
            """
        # חשב את היום של זמן ההגעה
        arrival_day = self.arrivalTime // 1440 +1

        # חשב את היום האחרון לשהייה
        last_day = arrival_day + self.stayDuration

        # חשב את היום הנוכחי
        current_day = currentTime

        # בדוק אם היום הנוכחי הוא היום האחרון לשהייה
        return current_day == last_day

    def isFirstDay(self, currentTime):
        """
        Check if it's the first day of the group's stay.
        :param currentTime: הזמן הנוכחי במונחי ימים.
        :return: True אם זה היום הראשון לשהייה, אחרת False.
        """
        # חשב את היום של זמן ההגעה
        arrival_day = self.arrivalTime // 1440 + 1

        # חשב את היום הנוכחי
        current_day = currentTime

        # בדוק אם היום הנוכחי הוא היום הראשון לשהייה
        return current_day == arrival_day
    def initialize_activities_dictionary(self):
        for customer in self.customers:
            activity_templates = {
                "family": {"pool": [False, 0], "bar": [False, 0]},
                "couple": {"spa": [False, 0], "pool": [False, 0]},
                "individual": {"spa": [False, 0], "bar": [False, 0], "pool": [False, 0]}
            }

    def update_day(self):
        self.currentDay += 1
        for customer in self.customers:
            customer.currentDay += 1

    def booking_Rank(self):
        rank_sum = 0
        rank_sum = sum(customer.rank for customer in self.customers)
        return rank_sum / self.num_customers


    def maxWaitingTimeInQ(self):
        if self.groupType == "family":
            return 10
        elif self.groupType == "couple":
            return 15
        elif self.groupType == "individual":
            return 20

    def updateRankCheckIn(self, starting_check_in_time):
        waitingInQueue = starting_check_in_time - self.arriveTime
        for customer in self.customers:
            customer.update_rank((waitingInQueue // 20) * 0.02)

    def updateRankBreakfast(self, starting_breakfast_time):
        waitingInQueue = starting_breakfast_time - self.breakfastArrivalTimes
        for customer in self.customers:
            customer.update_rank((waitingInQueue // 20) * 0.02)

    def updateRankExtendedQueue(self):
        for customer in self.customers:
            customer.update_rank(0.03)

    def booking_cost(self, room_type):
        total_expenses = 0
        if room_type == "Suite":
            total_expenses += self.stayDuration * 370
        else:
            total_expenses += self.stayDuration * 250

        for customer in self.customers:
            total_expenses += customer.get_expenses()

        ##print(f"Total group expenses: {total_expenses}")
        return total_expenses

class Facilities:  # spa, pool, and breakfast activities
    def __init__(self, activityType, maxCapacity):
        self.activityType = activityType  # Type of the activity (e.g., spa, pool, breakfast)
        self.maxCapacity = maxCapacity  # Maximum capacity of the activity
        self.currentOccupancy = 0  # Current number of participants
        self.activityQueue = []  # Queue for guests waiting to participate
        self.groupListActivity = []  # List of groups currently in the activity

    def checkActivityAvailabilityforagroup(self, booking):
        requiredCapacity = booking.getGroupSize()  # גודל הקבוצה
        return self.currentOccupancy + requiredCapacity <= self.maxCapacity

    def checkActivityAvailabilityforagust(self):
        requiredCapacity = 1  # מקום נדרש ללקוח יחיד
        return self.currentOccupancy + requiredCapacity <= self.maxCapacity


    def checkIfQueueIsNotEmpty(self):
        """
        Check if there are guests in the queue.
        """
        return len(self.activityQueue) > 0

    def addCustomerToActivity(self, num_of_guests):
        """
        Mark spaces in the pool as occupied for a group (Booking) or an individual (Customer).
        :param obj: אובייקט מסוג Booking או Customer.
        """

        self.currentOccupancy += num_of_guests

    def endCustomerActivity(self, num_of_guests):

        self.currentOccupancy -= num_of_guests
        ##print(f"Freed {num_of_guests} spaces from the activity. Current occupancy: {self.currentOccupancy}")

    def checkIfInQueue(self, customer):
        """
        Check if a customer is in the queue.
        """
        return customer in self.activityQueue

    def addToActivityQueue(self, customer):
        """
        Add a customer to the queue.
        """
        if customer not in self.activityQueue:
            self.activityQueue.append(customer)

    def removeFromQueue(self, customer):
        """
        Remove a customer from the queue.
        """
        if customer in self.activityQueue:
            self.activityQueue.remove(customer)

class Spa(Facilities):
    def __init__(self):
        super().__init__(activityType="Spa", maxCapacity=30)

class Pool(Facilities):
    def __init__(self):
        super().__init__(activityType="Pool", maxCapacity=50)


class Bar:
    def __init__(self):
        """
        Initialize the bar with two barmen and an empty queue.
        """
        self.barQueue = []  # Queue of guests waiting at the bar
        self.num_barmen = 2  # Number of barmen
        self.barmen_states = [False] * 2

      # Barmen availability states (False = available, True = busy)

    def findAvailableBarman(self):
        """
        Find an available barman.
        :return: Index of an available barman if found, otherwise None.
        """
        for i, is_busy in enumerate(self.barmen_states):
            if not is_busy:
                return i
        return None

    def setBarmanStatus(self, barman_index, status):
        """
        Update the status of a barman.
        :param barman_index: Index of the barman to update.
        :param is_busy: True if the barman is busy, False if available.
        """
        self.barmen_states[barman_index] = status


    def isInQueue(self, customer):
        """
        Check if a customer is already in the bar queue.
        """
        return customer in self.barQueue

class Hotel:
    def __init__(self):
        self.public_open = False#used but maybe delete
        self.servers_busy = 0#dosnt used maybe delete
        self.check_in_queue = []#used
        self.check_out_queue = []#used
        self.lobby_queue = []#used
        self.num_servers = 2  # מספר השרתים
        self.server_states = [False] * self.num_servers
        #self.count_people_checkin = 0  #todo:delete

        self.family_rooms = [Room("family") for _ in range(30)]  # 30 חדרי משפחה
        self.triple_rooms = [Room("triple") for _ in range(40)]  # 40 חדרי טריפל
        self.couple_rooms = [Room("couple") for _ in range(30)]  # 30 חדרי זוג
        self.suite_rooms = [Room("suite") for _ in range(10)]  # 10 סוויטות
        self.free_rooms_count = 110
        self.do_today_checkout=0#todo:delete
        self.nothaveroom=0
        self.total_customers=0#todo:delete

        self.tables = [Table() for _ in range(12)]
        self.breakfast_queue = []  # Guests waiting for breakfast
        self.count_pepole_checkout_after_breakfast=0#todo:delete
        self.count_pepole_brekfast_done=0 #todo:delete
        self.didnt_go_to_breakfast=0#todo:delete
        self.go_to_breakfast = 0  # todo:delete
        self.groups_from_last_Day=0 # todo:delete
        self.group_checked_out=0
        self.count_pepole_NObrekfast_checkout =0

        self.rate_for_breakfast=0#used
        self.daily_rank = 7#used
        self.hotelLambada = 9.8
        self.total_wait_forthisday=[]#used
         # Initial rank of the hotel

        self.rank_feedback = []#used
###########facilities####
        self.facilities = self.initializeFacilities()
        self.count_of_booking_go_to_pool_firstday=0#todo:delete
        self.count_of_booking_dont_go_to_pool_firstday = 0#todo:delete

        self.bar = Bar()
        self.count_Customers_family_go_to_pool=0
        self.count_Customers_family_go_to_bar=0
        self.count_Customers_family_dont_go_activity=0
        self.count_day_choose_activity=0
        self.breakfast_list = []




    ############rooms check in and check out#####################################################
    def check_and_assign_room(self, booking):
        """
        בודקת אם יש חדר פנוי עבור ההזמנה, ואם יש, מקצה אותו.
        :param booking: אובייקט ההזמנה.
        :return: מזהה החדר שהוקצה אם נמצא חדר, אחרת None.
        """
        booking_size = booking.getGroupSize()

        # בחירת רשימת חדרים מתאימה לפי גודל הקבוצה
        if booking_size >= 4:
            room_list = self.family_rooms
        elif booking_size == 3:
            room_list = self.triple_rooms
        elif booking_size == 2:
            room_list = self.suite_rooms if sampleIsSuite(2) else self.couple_rooms
        elif booking_size == 1:
            room_list = self.suite_rooms if sampleIsSuite(1) else self.couple_rooms

        # חיפוש חדר פנוי ברשימה
        for room in room_list:
            if room.isAvailable():
                room.bookRoom(booking)  # הקצאת החדר להזמנה
                return room.roomId  # מחזיר את מזהה החדר שהוקצה

        # אם לא נמצא חדר פנוי
        return None

    def collectBreakfastBookings(self):
        """
        אוספת את כל ההזמנות הפעילות ומעדכנת את breakfast_list.
        """
        self.breakfast_list = []  # אתחול הרשימה
        for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]:
            for room in room_list:
                booking = room.getCurrentBooking()
                if booking:  # אם יש הזמנה פעילה
                    self.breakfast_list.append(booking)
        print(f"Breakfast list updated: {len(self.breakfast_list)} bookings.")

    def calculateAvailableRoomsByTypeAtMidnight(self, current_date):
        """
        חישוב מספר החדרים הפנויים לפי סוגים ב-00:00 בהתחשב בחדרים שיעזבו ב-11:00.
        :param current_date: תאריך היום הנוכחי (מספר ימים מאז ההתחלה).
        :return: מילון עם מספר החדרים הפנויים לכל סוג חדר.
        """
        available_rooms = { "family": 0, "triple": 0, "couple": 0, "suite": 0 }

        for room_list, room_type in [
            (self.family_rooms, "family"),
            (self.triple_rooms, "triple"),
            (self.couple_rooms, "couple"),
            (self.suite_rooms, "suite")
        ]:
            for room in room_list:
                booking = room.getCurrentBooking()

                # אם זה היום האחרון של ההזמנה, בצע צ'ק-אאוט וסמן את החדר כפנוי
                if booking and booking.isLastDay(current_date):
                    room.change_to_available_room()
                    available_rooms[room_type] += 1
                # אם החדר כבר פנוי
                elif room.isAvailable():
                    available_rooms[room_type] += 1

        total_available = sum(available_rooms.values())
        #print(f"Total available rooms: {total_available}")
        return available_rooms

    def count_free_rooms(self):
        """
        סופר את מספר החדרים הפנויים בכל המלון.
        :return: מספר החדרים הפנויים.
        """
        return sum(
            1 for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]
            for room in room_list if room.isAvailable()
        )

    def release_room(self, booking):
        """
        מחפש ומשחרר את החדר של ההזמנה הנתונה.
        :param booking: אובייקט ההזמנה.
        """
        for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]:
            for room in room_list:
                if room.getCurrentBooking() == booking:
                    room.change_to_available_room()  # מסמן את החדר כפנוי
                    #print(f"Booking {booking.bookingId} checked out. Room {room.roomId} is now free.")
                    return
        #print(f"No room found for Booking {booking.bookingId}.")

    def find_available_server(self):
        for i, busy in enumerate(self.server_states):
            if not busy:
                return i
        return None

    def assign_to_server(self, server_id ):
        self.server_states[server_id] = True
####################################breakfast  ####################################################
    def find_available_table(self):
        """
        מחזיר את האינדקס של השולחן הפנוי הראשון או None אם אין שולחן פנוי.
        """
        for index, table in enumerate(self.tables):
            if not table.is_occupied:
                return index
        return None
####################update everyday hotel rank##########################################################
    def update_daily_rank(self):
        """
        עדכון הדירוג היומי לפי משוב הלקוחות.
        """
        if self.rank_feedback:  # אם יש דירוגים
            self.daily_rank = sum(self.rank_feedback) / len(self.rank_feedback)-self.rate_for_breakfast
            ##print(f"Updated review with - satisfaction from breakfast rank: {self.daily_rank}")
            total_waiting_time = sum(self.total_wait_forthisday)

            # חישוב עונש על זמני ההמתנה
            penalty = (total_waiting_time // 20) * 0.02  # כל 20 דקות מורידות 0.2 מהדירוג
            self.daily_rank = max(0, self.daily_rank - penalty)  # דירוג לא יורד מתחת ל
            # הדפסה
            ##print(f"Total waiting time for this day: {total_waiting_time} minutes")
            ##print(f"Updated daily rank: {self.daily_rank}")

            # איפוס המערך ליום הבא
            self.total_wait_forthisday = []
            self.rank_feedback = []  # איפוס רשימת הדירוגים
            self.rate_for_breakfast = 0

        else:
            self.daily_rank = 7  # אם אין דירוגים, שומרים על הדירוג ההתחלתי

    def get_daily_rank(self):#todo:delete
        return self.daily_rank



    def calculate_lambda(self,available_rooms):
        alpha = 20
        R_total = 110
        beta_1 = 1.5
        beta_2 = 2
        R_available = available_rooms
        H = self.daily_rank
        R_indicator=self.is_room_available_indicator()

        if R_available == 0:
            self.hotelLambada = 0  # אין חדרים פנויים => אין הגעת לקוחות
        else:
            self.hotelLambada = alpha * ((R_available / R_total) ** beta_1) * ((H / 10) ** beta_2)*R_indicator

        return self.hotelLambada

    def get_hotal_lambda(self):
        return self.hotelLambada

    def is_room_available_indicator(self):
        """
        מחזיר 1 אם לפחות חדר אחד פנוי, אחרת 0.
        """
        return 1 if self.count_free_rooms() > 0 else 0

##################################facalities#####################################
    def initializeFacilities(self):
        """
        Create facilities including the pool and spa.
        """
        return {
            "pool": Pool(),  # בריכה עם 50 מקומות
            "spa": Spa()  # ספא עם 30 מקומות
        }

    def getFacility(self, facility_name):
        """
        Get a specific facility by name.
        :param facility_name: שם המתקן (pool, spa).
        :return: אובייקט המתקן או None אם לא קיים.
        """
        return self.facilities.get(facility_name)

    def resetAllBookingsDailyActivities(self):
        """
        מאפסת את יומני הפעילויות של כל ההזמנות שנמצאות בחדרים במלון.
        """
        for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]:
            for room in room_list:
                if room.currentBooking:  # אם יש הזמנה פעילה בחדר
                    room.currentBooking.resetDailyActivities()  # מאפס את יומן הפעילויות
                    ##print(f"Daily activities reset for Booking {room.currentBooking.bookingId}.")

    def count_family_customers(self, time):
        """
        סופר כמה לקוחות מסוג משפחות יש במלון.
        :return: מספר הלקוחות מסוג משפחות.
        """
        family_customers_count = 0

        for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]:
            for room in room_list:
                booking = room.currentBooking
                if booking and booking.groupType == "family" and not booking.isFirstDay(time) and not booking.isLastDay(time):
                    family_customers_count += len(booking.customers)

        return family_customers_count

    def print_all_customers_status(self,current_time):
        """
        מדפיסה את מצב כל הלקוחות על בסיס החדרים במלון, כולל פעילותם הנוכחית.
        """
        print(f"\n--- Customer Status at {current_time}:00 ---")
        total_customers = 0

        # מעבר על כל סוגי החדרים במלון
        for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]:
            for room in room_list:
                if room.currentBooking and not room.currentBooking.isFirstDay(current_time):  # אם יש הזמנה בחדר
                    for customer in room.currentBooking.customers:  # מעבר על כל הלקוחות בהזמנה
                        total_customers += 1
                        print(f"Customer {customer.customerId}: {customer.daily_activities}")

        print(f"Total customers for activities: {total_customers}")


    def get_total_customers_in_breakfast_list(self):
        """
        מחזירה את סך כל הלקוחות ברשימת ארוחות הבוקר.
        """
        return sum(booking.getGroupSize() for booking in self.breakfast_list)


import heapq

class Simulation:
    def __init__(self, simulationTime):
        """
        Initialize the simulation with hotel instance and event queue.
        :param simulationTime: Total time for the simulation (in minutes).
        """
        self.simulationTime = simulationTime  # משך זמן הסימולציה
        self.Hotel = Hotel()  # אובייקט המלון לניהול כל התהליכים
        self.clock = 0  # שעון הסימולציה
        self.event_list = []  # רשימת אירועים (תור עדיפויות)
        self.total_waiting_time = 0  # מצטבר של זמני ההמתנה של כל הלקוחות

    def scheduleEvent(self, event):
        """
        Schedule a new event by adding it to the priority queue.
        """
        heapq.heappush(self.event_list, event)

    def run(self):
        """
        Run the simulation by processing events until the end of simulation time.
        """
        self.scheduleEvent(OpenHotelEvent(480))
        self.scheduleEvent(OpenBreakfast(1830))#first meal

        self.scheduleEvent(closeHotelDayEvent(24*60))
        self.scheduleEvent(calcbrefasteachday(12 * 60))
        self.scheduleEvent(calccheckout(14 * 60))
        self.scheduleEvent(FamilyActivitySummaryEvent(47 * 60))


        # עיבוד האירועים עד שהסימולציה מסתיימת
        while self.event_list and self.clock < self.simulationTime:
            event = heapq.heappop(self.event_list)  # שליפת האירוע הבא
            self.clock = event.time  # עדכון השעון לזמן האירוע
            event.handle(self)  # טיפול באירוע

        # הצגת תוצאות הסימולציה
        self.displaySimulationResults()

    def displaySimulationResults(self):
        """
        Display the final results of the simulation.
        """  # סך כל הקבוצות שהתארחו במלון
        #print(f"Lobby queue size: {len(self.Hotel.lobby_queue)}")



# הפעלת הסימולציה מחוץ למחלקה
if __name__ == "__main__":
    # יצירת מופע של הסימולציה למשך 10 ימים
    check = Simulation(60 * 24 * 5)  # 10 ימים
    check.run()