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

    def performCheckOut(self):

        """
        מסמן את החדר כפנוי ומשחרר את ההזמנה הנוכחית.
        """
        if self.currentBooking:  # אם יש הזמנה פעילה
            print(f"Room of type {self.roomType} is now free.")
            self.currentBooking = None  # שחרור ההזמנה
            self.available = True  # סימון החדר כפנוי
        else:
            print(f"Room of type {self.roomType} is already free.")


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




class Booking:
    totalBookings = 0  # Static variable to track the total number of bookings

    def __init__(self, arrivalTime):
        """
        Initialize a new booking with group details and activities.
        """
        Booking.totalBookings += 1
        self.bookingId = Booking.totalBookings
        self.customers = []  # Changed to lowercase for consistency
        self.numGuests = sampleCustomerCount()
        self.stayDuration = sampleStayDuration()
        self.arrivalTime = arrivalTime
        self.breakfastArrivalTimes = []  # To store breakfast times for each day
        self.groupType = self.determineGroupType()
        self.breakfastArrivalTime = None
        self.hasCheckedOut = False

        # Create customers based on the group category

    def __lt__(self, other):
        """
        השוואה בין הזמנות על בסיס זמן הגעה.
        """
        return self.arrivalTime < other.arrivalTime

    def initializeDailyActivities(self):
        """
        Set up daily activities for customers based on group category.
        """
        activityMapping = {
            "family": {"pool": [False, 0], "bar": [False, 0]},
            "triple": {"pool": [False, 0], "bar": [False, 0]},
            "couple": {"spa": [False, 0], "pool": [False, 0]},
            "one": {"spa": [False, 0], "bar": [False, 0], "pool": [False, 0]}
        }
        for customer in self.customers:
            customer.dailyActivities = activityMapping.get(self.groupType, {}).copy()



    def getGroupSize(self):
        """
        Return the size of the group.
        """
        return self.numGuests

    def getDurationtime(self):
        return self.stayDuration
    def determineGroupType(self):
        """
        Categorize the group based on its size.
        """
        if self.numGuests == 3:
            return "triple"
        elif self.numGuests >= 4:
            return "family"
        elif self.numGuests == 2:
            return "couple"
        return "one"


    def isFirstDay(self, currentTime):
        """
        Check if it's the first day of the group's stay.
        """
        return currentTime // (24 * 60) == self.arrivalTime // (24 * 60)

    def isLastDay(self, currentTime):
        """
        Check if it's the last day of the group's stay.
        """
        return currentTime // (24 * 60) == (self.arrivalTime // (24 * 60) + self.stayDuration)

class hotelSimulation:
    def __init__(self):
        self.public_open = False
        self.check_in_open = False
        self.check_out_open = False
        self.num_servers = 2
        self.servers_busy = 0
        self.check_in_queue = []
        self.check_out_queue = []
        self.lobby_queue = []
        self.total_guest_groups=0
        self.assignRoomscount=0
        self.count_chekin_queue=0
        self.num_servers = 2  # מספר השרתים
        self.server_states = [False] * self.num_servers
        self.nothaveroom=0
        self.count_pepole_checkin = 0  #

        self.family_rooms = [Room("family") for _ in range(30)]  # 30 חדרי משפחה
        self.triple_rooms = [Room("triple") for _ in range(40)]  # 40 חדרי טריפל
        self.couple_rooms = [Room("couple") for _ in range(30)]  # 30 חדרי זוג
        self.suite_rooms = [Room("suite") for _ in range(10)]  # 10 סוויטות
        self.free_rooms_count = 110
        self.do_today_checkout=0

        self.tables = [Table() for _ in range(12)]
        self.breakfast_queue = []  # Guests waiting for breakfast
        self.count_pepole_brekfast_checkout=0#todo:delelte
        self.count_pepole_brekfast_done=0 #todo:delete
        self.didnt_go_to_breakfast=0#todo:delete
        self.go_to_breakfast = 0  # todo:delete
        self.rate_for_breakfast=0
        self.daily_rank = 7
        self.hotelLambada = self.calculate_lambda(110)
        self.total_wait_forthisday=[]
         # Initial rank of the hotel

        self.rank_feedback = []

    def calculate_lambda(self,available_rooms):
        alpha = 20
        R_total = 110
        beta_1 = 1.5
        beta_2 = 2
        R_available = available_rooms
        H = self.daily_rank

        if R_available == 0:
            self.hotelLambada = 0  # אין חדרים פנויים => אין הגעת לקוחות
        else:
            self.hotelLambada = alpha * ((R_available / R_total) ** beta_1) * ((H / 10) ** beta_2)

        return self.hotelLambada

    def get_hotal_lambda(self):
            return self.hotelLambada


    def check_and_assign_room(self, booking):
            """
            בודקת אם יש חדר פנוי עבור ההזמנה, ואם יש, מקצה אותו.
            :param booking: אובייקט ההזמנה.
            :return: מזהה החדר שהוקצה אם נמצא חדר, אחרת None.
            """
            booking_size = booking.getGroupSize()
            room_list = []

            # בחירת רשימת חדרים מתאימה לפי גודל הקבוצה
            if booking_size >= 4:
                room_list = self.family_rooms  # חדרי משפחות
            elif booking_size == 3:
                room_list = self.triple_rooms  # חדרי טריפל
            elif booking_size == 2:
                # בדיקה אם אפשר להקצות סוויטה או חדר זוגי
                room_list = self.suite_rooms if sampleIsSuite(2) else self.couple_rooms
            elif booking_size == 1:
                # בדיקה אם אפשר להקצות סוויטה או חדר יחיד
                room_list = self.suite_rooms if sampleIsSuite(1) else self.couple_rooms

            # חיפוש חדר פנוי ברשימה
            for room in room_list:
                if room.isAvailable():
                    room.bookRoom(booking)  # הקצאת החדר להזמנה
                    print(f"Assigned room {room.roomId} to booking {booking.bookingId}.")
                    return room.roomId  # מחזיר את מזהה החדר שהוקצה

            #אם לא נמצא חדר פנוי
            print(f"Total free rooms: {self.count_free_rooms()}")
            print(f"No room available for booking  {booking.bookingId}.")
            return None


    def calculateAvailableRoomsByTypeAtMidnight(self, current_date):
            """
            חישוב מספר החדרים הפנויים לפי סוגים ב-00:00 בהתחשב בחדרים שיעזבו ב-11:00.
            :param current_date: תאריך היום הנוכחי (מספר ימים מאז ההתחלה).
            :return: מילון עם מספר החדרים הפנויים לכל סוג חדר.
            """
            available_rooms = {
                "family": 0,
                "triple": 0,
                "couple": 0,
                "suite": 0,
            }

            # בדוק חדרים שמתפנים היום ב-11:00 עבור כל סוג חדר
            for room_list, room_type in [
                (self.family_rooms, "family"),
                (self.triple_rooms, "triple"),
                (self.couple_rooms, "couple"),
                (self.suite_rooms, "suite")
            ]:
                for room in room_list:
                    booking = room.getCurrentBooking()

                    # אם זה היום האחרון של ההזמנה, בצע צ'ק-אאוט וסמן את החדר כפנוי
                    if booking and booking.isLastDay(current_date * 24 * 60):
                        room.performCheckOut()
                        available_rooms[room_type] += 1
                    # אם החדר כבר פנוי
                    elif room.isAvailable():
                        available_rooms[room_type] += 1
            total_available = sum(available_rooms.values())
            return total_available

    def count_free_rooms(self):#used
        return sum(
            1 for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms] for room in
            room_list if room.isAvailable())

    def is_server_available(self):
        """בודק אם יש שרת פנוי"""
        return any(not busy for busy in self.servers_busy)

    def find_available_server(self):
        for i, busy in enumerate(self.server_states):
            if not busy:
                return i
        return None

    def assign_to_server(self, time, server_id,booking ):
        self.server_states[server_id] = True

    def get_arrival_rate(self):
        return self.arrival_rate

    def set_public_status(self, status):
        self.public_open = status

    def set_check_out_status(self, status):
        self.check_out_open = status

    def setCheckInOpen(self, status):
        """
        Set the status of the check-in process (open/close).
        :param status: True to open, False to close.
        """
        self.check_in_open = status


    def assignRoom(self, booking):
        """
        Assign a room to the given booking based on the group size.
        :param booking: Booking object containing group details.
        :return: True if a room was successfully assigned, False otherwise.
        """
        booking_size = booking.getGroupSize()

        # הגדרת סדר החיפוש לפי גודל הקבוצה
        if booking_size >= 4:
            room_list = self.family_rooms  # חדרי משפחות ל-4 ומעלה
        elif booking_size == 3:
            room_list = self.triple_rooms  # חדרי טריפל ל-3 אורחים
        elif booking_size == 2:
            # בדיקה אם ההזמנה מתאימה לסוויטה
            if sampleIsSuite(2):
                room_list = self.suite_rooms
            else:
                room_list = self.couple_rooms
        else:
            # בדיקה אם ההזמנה מתאימה לסוויטה ליחיד
            if sampleIsSuite(1):
                room_list = self.suite_rooms
            else:
                room_list = self.couple_rooms

        # חיפוש החדר הפנוי הראשון והקצאתו
        for room in room_list:
            if room.isAvailable():
                room.bookRoom(booking)
                self.assignRoomscount += 1
                return True
            self.nothaveroom += 1  # אם לא נמצא חדר מתאים
            return False

    def release_room(self, booking):
        """
        מחפש ומשחרר את החדר של ההזמנה הנתונה.
        :param booking: אובייקט ההזמנה.
        """
        for room_list in [self.family_rooms, self.triple_rooms, self.couple_rooms, self.suite_rooms]:
            for room in room_list:
                if room.currentBooking == booking:
                    room.performCheckOut()  # מסמן את החדר כפנוי
                    print(f"Booking {booking.bookingId} checked out. Room {room.roomId} is now free.")
                    return
        print(f"No room found for Booking {booking.bookingId}.")

    def setPublicAccess(self,status):
        self.public_open = status
########breakfast#######
    def find_available_table(self):
        """
        מחזיר את האינדקס של השולחן הפנוי הראשון או None אם אין שולחן פנוי.
        """
        for index, table in enumerate(self.tables):
            if not table.is_occupied:
                return index
        return None



    def update_daily_rank(self):
        """
        עדכון הדירוג היומי לפי משוב הלקוחות.
        """
        if self.rank_feedback:  # אם יש דירוגים
            self.daily_rank = sum(self.rank_feedback) / len(self.rank_feedback)-self.rate_for_breakfast
        else:
            self.daily_rank = 7  # אם אין דירוגים, שומרים על הדירוג ההתחלתי
        self.rank_feedback = []  # איפוס רשימת הדירוגים
        self.rate_for_breakfast = 0




    def update_wait_total_for_Rank(self):
        total_waiting_time = sum(self.total_wait_forthisday)

        # חישוב עונש על זמני ההמתנה
        penalty = (total_waiting_time // 20) * 0.02  # כל 20 דקות מורידות 0.2 מהדירוג
        self.daily_rank = max(0, self.daily_rank - penalty)  # דירוג לא יורד מתחת ל-0

        # הדפסה
        print(f"Total waiting time for this day: {total_waiting_time} minutes")
        print(f"Updated daily rank: {self.daily_rank}")

        # איפוס המערך ליום הבא
        self.total_wait_forthisday = []



import heapq

class Simulation:
    def __init__(self, simulationTime):
        """
        Initialize the simulation with hotel instance and event queue.
        :param simulationTime: Total time for the simulation (in minutes).
        """
        self.simulationTime = simulationTime  # משך זמן הסימולציה
        self.hotelSimulation = hotelSimulation()  # אובייקט המלון לניהול כל התהליכים
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
        # פתיחת המלון ב-8 בבוקר
        self.scheduleEvent(closeHotelDayEvent(60*24))

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
        """
        print("Total guest groups:", self.hotelSimulation.total_guest_groups)  # סך כל הקבוצות שהתארחו במלון
        print(f"Lobby queue size: {len(self.hotelSimulation.lobby_queue)}")
        print(f"pepole from brekfast to checkout: ", self.hotelSimulation.count_pepole_brekfast_checkout)
        print(f"brekfast done :",self.hotelSimulation.count_pepole_brekfast_done)
        print(f"no room  :", self.hotelSimulation.nothaveroom)
        print(f"chrckindone  :", self.hotelSimulation.count_pepole_checkin)


# הפעלת הסימולציה מחוץ למחלקה
if __name__ == "__main__":
    # יצירת מופע של הסימולציה למשך 10 ימים
    check = Simulation(60 * 24 * 10)  # 10 ימים
    check.run()
