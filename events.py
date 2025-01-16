import heapq

from samples import *
from yuvaltry2 import*



class Event:
    def __init__(self, time):
        self.time = time

    def __lt__(self, other):
        return self.time < other.time

    def handle(self, simulation):
        raise NotImplementedError("Handle method must be implemented by subclasses")

class OpenHotelEvent(Event):
   # open the hotel to guests at 8am
    def handle(self, simulation):
        simulation.Hotel.setPublicAccess(True)
        simulation.scheduleEvent(CloseCustomerArrivalEvent(self.time + 9 * 60))
        next_arrival_time = self.time + sampleCustomerArrival(simulation.Hotel.get_hotal_lambda())
        arrival_end_time = (self.time // 1440) * 1440 + 17 * 60  # סיום היום בשעה 17:00
        if next_arrival_time < arrival_end_time:
            simulation.scheduleEvent(CheckInArrivalEvent(next_arrival_time))
        # תזמון הצ'ק-אין הראשון ב-15:00
        check_in_start_time = self.time+7 * 60  # 15:00 ביום הראשון
        simulation.scheduleEvent(CheckInDepartureEvent(check_in_start_time, None))


class closeHotelDayEvent(Event):
        # open the hotel to guests at 00:00
    def handle(self, simulation):
        current_date = self.time // (24 * 60)  # מחלקים את הזמן הכולל למקטעי ימים


        available_rooms=simulation.Hotel.count_free_rooms()
        simulation.Hotel.resetAllBookingsDailyActivities()
        print(f"The total rooms occipud for the end of the day  : {current_date } is: {110-available_rooms}")
        print(f"the total people who did check in today is {simulation.Hotel.count_people_checkin }")
        print(f"The total groups go to pool after checkin first day : {simulation.Hotel.count_of_booking_go_to_pool_firstday} ")#todo:delete
        print(
            f"The total groups dont go to pool after checkin first day : {simulation.Hotel.count_of_booking_dont_go_to_pool_firstday} ")#todo:delete
        available_rooms_nextday = simulation.Hotel.calculateAvailableRoomsByTypeAtMidnight(current_date + 1)
        simulation.Hotel.update_daily_rank()
        current_lamda= simulation.Hotel.calculate_lambda(available_rooms)
        print(f"The lamda for tomorow is   : {current_date+1} and lamda is: {current_lamda}")
        daily_rank=simulation.Hotel.get_daily_rank()
        print(f"The  daily rank from  the day   : {current_date } and daily rank is is for day :{current_date+1 }is: {daily_rank}")
        simulation.scheduleEvent(closeHotelDayEvent(self.time + 24 * 60))
        simulation.Hotel.group_checked_out = 0
        simulation.Hotel.count_pepole_NObrekfast_checkout = 0
        simulation.Hotel.count_pepole_checkout_after_breakfast = 0
        simulation.Hotel.didnt_go_to_breakfast = 0
        simulation.Hotel.go_to_breakfast = 0
        simulation.Hotel.count_of_booking_dont_go_to_pool_firstday=0#todo:delete
        simulation.Hotel.count_of_booking_go_to_pool_firstday = 0#todo:delete
        simulation.Hotel.count_people_checkin =0


class CloseCustomerArrivalEvent(Event):  # close the hotel to guests at 5pm
    def handle(self, simulation):
        simulation.Hotel.setPublicAccess(False)
        current_date = self.time // (24 * 60) +1 # מחלקים את הזמן הכולל למקטעי ימים
        simulation.scheduleEvent(OpenHotelEvent(self.time + 15 * 60))  # schedule reopening at 8am




class CheckInArrivalEvent(Event):
    def handle(self, simulation):
        # יצירת הזמנה חדשה והוספתה לתור הלובי
        next_arrival_time = self.time + sampleCustomerArrival(simulation.Hotel.get_hotal_lambda())
        local_time = next_arrival_time % 1440  # השעה הנוכחית במונחי דקות ביום

        # בדיקה אם השעה היא בין 08:00 ל-17:00
        check_in_start_time = 8 * 60  # 08:00 במונחי דקות
        check_in_end_time = 17 * 60  # 17:00 במונחי דקות

        if  (check_in_start_time <= local_time < check_in_end_time):
        # חישוב זמן ההגעה הבא
            simulation.scheduleEvent(CheckInArrivalEvent(next_arrival_time))

        booking = Booking(next_arrival_time)
        if simulation.Hotel.check_and_assign_room(booking):
            simulation.Hotel.total_guest_groups+=1
            heapq.heappush(simulation.Hotel.lobby_queue, booking)
            print(f"Booking {booking.bookingId} added to lobby queue at time {self.time}.")

        # תזמון ההגעה הבאה אם יש זמן נוסף בסימולציה

        else:
            simulation.Hotel.nothaveroom+=1

class CheckInDepartureEvent(Event):
    def __init__(self, time, booking=None):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        # אם אין לקוחות בתור, סיים את האירוע
        if not simulation.Hotel.lobby_queue:
            print("No more guests in the lobby queue.")
            return

        # שליפת האורח הראשון בתור
        if self.booking is None:  # אירוע ראשוני
            self.booking = heapq.heappop(simulation.Hotel.lobby_queue)

        # חישוב זמן השירות
        service_time = sampleCheckIn()
        service_end_time = self.time + service_time

        # בדיקה אם זמן השירות חורג משעה 20:00
        if service_end_time % 1440 > 20 * 60:
            print(f"Time {service_end_time % 1440} exceeds 20:00. Releasing room for Booking {self.booking.bookingId}.")
            simulation.Hotel.release_room(self.booking)
        else:
            # הקצאת שירות לאורח
            simulation.Hotel.count_people_checkin += 1
            print(f"Booking {self.booking.bookingId} received service at time {self.time}.")
            waitingTime = self.time - self.booking.arrivalTime
            if waitingTime > 20:
                rankDecrease = (waitingTime // 20) * 0.02
                for customer in self.booking.customers:
                    customer.update_rank(rankDecrease)
            # תזמון ארוחות בוקר לכל יום שהייה
            simulation.scheduleEvent(FirstDayPoolEvent(self.time,self.booking))
            start_day = int(self.booking.arrivalTime // 1440 + 1)
            end_day = int(self.booking.arrivalTime // 1440 + 1 + self.booking.stayDuration)

            for day in range(start_day, end_day + 1):
                breakfast_time = day * 1440 + (6.5 * 60) + sampleBreakfastRate()
                simulation.scheduleEvent(BreakfastArrivalEvent(breakfast_time, self.booking))

            # תזמון צ'ק-אאוט ביום האחרון בשעה 11:00
            checkout_time = (start_day + self.booking.stayDuration) * 1440 + 11 * 60
            simulation.scheduleEvent(CheckOutReminderEvent(checkout_time, self.booking))

        # טיפול באורח הבא בתור
        if simulation.Hotel.lobby_queue:
            next_booking = heapq.heappop(simulation.Hotel.lobby_queue)
            simulation.scheduleEvent(CheckInDepartureEvent(service_end_time, next_booking))



class CheckoutArrivalEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        """
        Handle the checkout event for the group.

        """
        feedback = random.randint(1, 10)
        simulation.Hotel.rank_feedback.append(feedback)
        server = simulation.Hotel.find_available_server()
        if server is not None:

            simulation.Hotel.assign_to_server(server)
            service_time = self.time + sampleCheckOut()
            simulation.scheduleEvent(CheckOutDepartureEvent(service_time, server, self.booking))
        else:
            # Add to the priority queue (negative priority for max-heap behavior)
            simulation.Hotel.check_out_queue.append((self.time, self.booking))


class CheckOutDepartureEvent(Event):  # Add inheritance from Event
    def __init__(self, time, server_id, booking):
        super().__init__(time)
        self.server_id = server_id
        self.booking = booking

    def handle(self, simulation):
        """
        Handle the departure event after checkout.
        """

        simulation.Hotel.group_checked_out += 1
        # Mark the server as free or assign to the next booking in queue
        if simulation.Hotel.check_out_queue:
            next_booking_time, next_booking = simulation.Hotel.check_out_queue.pop(0)
            service_time = self.time + sampleCheckOut()
            simulation.scheduleEvent(CheckOutDepartureEvent(service_time, self.server_id, next_booking))
        else:
            simulation.Hotel.server_states[self.server_id] = False



class BreakfastArrivalEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        breakfast_start_time = 6.5 * 60  # 6:30 במונחי דקות
        breakfast_end_time = 11 * 60    # 11:00 במונחי דקות
        local_time = self.time % 1440

        # בדיקה אם הזמן הוא במסגרת שעות פעילות חדר האוכל
        if not (breakfast_start_time <= local_time < breakfast_end_time):
            simulation.Hotel.didnt_go_to_breakfast += 1
            simulation.scheduleEvent(DailyActivityEvent(self.time, self.booking))

            #LISHLOAH LEPILOOTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            return

        available_table_index = simulation.Hotel.find_available_table()
        if available_table_index is not None:

            breakfast_duration = self.time + sampleBreakfastTime()

            simulation.Hotel.tables[available_table_index].set_status(True)
            print(f"Table seat {self.booking.bookingId} at table {available_table_index}")
            simulation.scheduleEvent(BreakfastDepartureEvent(breakfast_duration, self.booking, available_table_index))

        else:
            self.booking.breakfastArrivalTime = self.time
            simulation.Hotel.breakfast_queue.append(self.booking)

class BreakfastDepartureEvent(Event):
    def __init__(self, time, booking, table_id):
        super().__init__(time)
        self.booking = booking
        self.table_id = table_id

    def handle(self, simulation):
                # שחרור השולחן

        simulation.Hotel.go_to_breakfast += 1
        simulation.Hotel.tables[self.table_id].set_status(False)
        print(f"Table {self.table_id} is now available.")

        # בדיקה אם זה היום האחרון והשעה כבר 11:00
        local_time = self.time % 1440  # הזמן הנוכחי ביום
        if self.booking.isLastDay(self.time // 1440 + 1):
            if local_time >= 11 * 60:  # השעה 11:00 ומעלה
                print(f"Booking {self.booking.bookingId} is skipping breakfast and going directly to checkout.")
                simulation.Hotel.count_pepole_NObrekfast_checkout += 1
                self.booking.hasCheckedOut = True
                simulation.scheduleEvent(CheckoutArrivalEvent(self.time, self.booking))
                return

            # אם האורח התחיל ארוחת בוקר לפני 11:00, תזמן אותו לצ'ק-אאוט אחרי הארוחה
            print(f"Booking {self.booking.bookingId} will go to checkout after breakfast.")
            simulation.Hotel.count_pepole_checkout_after_breakfast += 1
            self.booking.hasCheckedOut = True
            simulation.scheduleEvent(CheckoutArrivalEvent(self.time, self.booking))

        for customer in self.booking.customers:
            if random.random() < 0.1:
                print(f"Booking {self.booking.bookingId} did not enjoy the breakfast.")
                rankDecrease=0.025
                customer.update_rank(rankDecrease)

        simulation.scheduleEvent(DailyActivityEvent(self.time, self.booking))


        # אם יש אנשים בתור, הושב אותם לשולחן שהתפנה
        if simulation.Hotel.breakfast_queue:
            next_booking = simulation.Hotel.breakfast_queue.pop(0)
            print(f"Booking {next_booking.bookingId} seated at table {self.table_id} from queue.")
            breakfast_duration = self.time + sampleBreakfastTime()
            simulation.scheduleEvent(BreakfastDepartureEvent(breakfast_duration, next_booking, self.table_id))
            wait_time=self.time-next_booking.breakfastArrivalTime
            if wait_time > 20:
                rankDecrease = (wait_time // 20) * 0.02
                for customer in self.booking.customers:
                    customer.update_rank(rankDecrease)




class CheckOutReminderEvent(Event):
    def __init__(self, time, booking):
       super().__init__(time)
       self.booking = booking

    def handle(self, simulation):
        # בדיקה אם האורח כבר ביצע צ'ק-אאוט
       if not self.booking.hasCheckedOut:
            simulation.Hotel.count_pepole_NObrekfast_checkout += 1
            print(f"Booking {self.booking.bookingId} missed breakfast, going to checkout.")
            self.booking.hasCheckedOut = True
            simulation.scheduleEvent(CheckoutArrivalEvent(self.time, self.booking))



class calcbrefasteachday(Event): #todo:delete
    def __init__(self, time):
        super().__init__(time)


    def handle(self, simulation):
        current_date = self.time // (24 * 60)  # מחלקים את הזמן הכולל למקטעי ימים
        print(f"The day for pepole arrive at : {current_date} ")
        print(f"The day is dont go to breakfast: {current_date+1} ,{simulation.Hotel.didnt_go_to_breakfast }")  # todo:delet
        print(f"The day is  go to breakfast: {current_date+1}, {simulation.Hotel.go_to_breakfast}")
        simulation.scheduleEvent(calcbrefasteachday(self.time+24*60))



class calccheckout(Event): #todo:delete
    def __init__(self, time):
        super().__init__(time)


    def handle(self, simulation):
        current_date = self.time // (24 * 60) +1 # מחלקים את הזמן הכולל למקטעי ימים
        print(f"The total people did checkout  {simulation.Hotel.group_checked_out} at day,{current_date} ")
        print(f"The total people did checkout NO BREAKFAST  {simulation.Hotel.count_pepole_NObrekfast_checkout} at day,{current_date} ")
        print(f"The total people did checkout YES BREAKFAST {simulation.Hotel.count_pepole_checkout_after_breakfast} at day,{current_date} ")
        simulation.scheduleEvent(calccheckout(self.time + 24 * 60))



class FirstDayPoolEvent(Event): #todo:recall from chek in depurtue
    def __init__(self, time,booking):
        super().__init__(time)
        self.booking = booking


    def handle(self, simulation):
        local_time=self.time%1440
        if local_time>19*60:
            simulation.Hotel.count_of_booking_dont_go_to_pool_firstday += 1#todo:delete
            return
        if not isinstance(self.booking, Booking):
            raise ValueError(f"Invalid type for booking in FirstDayPoolEvent: {type(self.booking)}")
        if simulation.Hotel.getFacility("pool").checkActivityAvailability(self.booking):
            simulation.Hotel.getFacility("pool").addCustomerToActivity(self.booking)
            service_time=self.time+samplePoolSpent()
            simulation.scheduleEvent(FirstDayPoolDepartureEvent(service_time, self.booking))
        else:
            simulation.Hotel.count_of_booking_dont_go_to_pool_firstday += 1#todo:delete
            return
class FirstDayPoolDepartureEvent(Event):
    def __init__(self, time,booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        print(f"the booking number who came to pool after check-in is {self.booking.bookingId}")#todo:delete
        simulation.Hotel.count_of_booking_go_to_pool_firstday+=1#todo:delete
        simulation.Hotel.getFacility("pool").endCustomerActivity(self.booking)#todo:delete


class DailyActivityEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        group_type = self.booking.checkGroupType()

        if group_type == "family":
            for customer in self.booking.customers:
                if np.random.rand() < 0.8:  # 80% בריכה
                    simulation.scheduleEvent(PoolEvent(self.time, customer))
                else:  # 20% בר
                    simulation.scheduleEvent(BarEvent(self.time, customer))

        elif group_type == "couple":
            if np.random.rand() < 0.7:  # 70% בריכה יחד
                for customer in self.booking.customers:
                    simulation.scheduleEvent(PoolEvent(self.time, customer))
            else:  # 30% אחד בבריכה והשני בחדר
                simulation.scheduleEvent(PoolEvent(self.time, self.booking.customers[0]))
                print(f"Customer {self.booking.customers[1].customerId} stayed in the room.")



        elif group_type == "individual":
            for customer in self.booking.customers:
                simulation.scheduleEvent(PoolEvent(self.time, customer))  # יחיד מתחיל בבריכה


class PoolEvent(Event):
    def __init__(self, time, customer):
        super().__init__(time)
        self.customer = customer

    def handle(self, simulation):
        local_time = self.time % 1440
        if local_time > 19 * 60:
            return
        if local_time<7*60:
            current_day = self.time // (24 * 60)
            next_opening_time = (current_day * 24 * 60) + 7*60
            simulation.scheduleEvent(PoolEvent(next_opening_time, self.customer))

        print(f"Customer {self.customer.customerId} from booking {self.customer.customerId} is at the pool.")
        facility = simulation.hotel.getFacility("pool")

        # עדכון המילון במצב הנוכחי

        self.customer.daily_activities["pool"][1] += 1  # העלאת מספר הפעמים שניסה להיכנס
        if simulation.Hotel.getFacility("pool").checkActivityAvailability(self.customer):
            simulation.Hotel.getFacility("pool").addCustomerToActivity(self.customer)
            service_time=self.time+samplePoolSpent()
            simulation.scheduleEvent(PoolDepartureEvent(service_time, self.customer))
        else:
            facility.addToActivityQueue(self.customer)
            simulation.scheduleEvent(RenegingEvent(self.time + self.customer.maxWaitingTime, self.customer, facility.activity_queue))


class BarEvent(Event):
    def __init__(self, time, customer):
        super().__init__(time)
        self.customer = customer

    def handle(self, simulation):
        available_barman = simulation.Hotel.findAvailableBarman()

        if available_barman:
            # אם יש ברמן זמין, הלקוח מתחיל לקבל שירות
            available_barman.setBarmanStatus(available_barman,True)
            print(f"Customer {self.customer.customerId} started bar service with {available_barman} at time {self.time}.")
            departure_time = self.time + sampleBarService()
            simulation.scheduleEvent(BarDepartureEvent(departure_time, self.customer, available_barman))
        else:
                simulation.Hotel.barQueue.append(self.customer)
                simulation.scheduleEvent(RenegingEvent(self.time + self.customer.maxWaitingTime, self.customer,simulation.Hotel.barQueue))
                print(f"Customer {self.customer.customerId} added to the bar queue at time {self.time}.")


class SpaEvent(Event):
    def __init__(self, time, customer):
        super().__init__(time)
        self.customer = customer

    def handle(self, simulation):
        local_time = self.time % 1440
        if local_time > 19 * 60:
            return
        if local_time < 7 * 60:
            current_day = self.time // (24 * 60)
            next_opening_time = (current_day * 24 * 60) + 7 * 60
            simulation.scheduleEvent(SpaEvent(next_opening_time, self.customer))
        print(f"Customer {self.customer.customerId} from booking ")
        facility = simulation.hotel.getFacility("spa")

        # עדכון המילון במצב הנוכחי
        self.customer.daily_activities["spa"][1] += 1  # העלאת מספר הפעמים שניסה להיכנס
        if simulation.Hotel.getFacility("spa").checkActivityAvailability(self.customer):
            simulation.Hotel.getFacility("spa").addCustomerToActivity(self.customer)
            service_time=self.time+sampleSpa()
            simulation.scheduleEvent(SpaDepartureEvent(service_time, self.customer))

        else:
            facility.addToActivityQueue(self.customer)
            simulation.scheduleEvent(RenegingEvent(self.time + self.customer.maxWaitingTime, self.customer, facility.activity_queue))


class PoolDepartureEvent(Event):
    def __init__(self, time, customer):
        super().__init__(time)
        self.customer = customer

    def handle(self, simulation):
        # קבלת האובייקט של הספא
        facility = simulation.hotel.getFacility("pool")

        # שחרור הלקוח מהפעילות
        facility.endCustomerActivity(self.customer)
        print(f"Customer {self.customer.customerId} left the pool at time {self.time}.")

        if facility.hasQueue():
            # הוצאת הלקוח הבא מהתור ומחיקתו
            next_customer = facility.queue.pop(0)  # הלקוח הראשון בתור

            # עדכון הפעילות ביומן של הלקוח
            next_customer.daily_activities["pool"][0] = True
            next_customer.daily_activities["pool"][1] += 1

            # חישוב זמן השירות ללקוח הבא
            service_time = self.time + facility.sampleServiceTime()

            # הכנסת הלקוח לפעילות
            facility.addCustomerToActivity(next_customer)
            print(f"Customer {next_customer.customerId} started pool activity at time {self.time}.")

            # תזמון אירוע עזיבת הבריכה עבור הלקוח הבא
            simulation.scheduleEvent(PoolDepartureEvent(service_time, next_customer))


class BarDepartureEvent(Event):
    def __init__(self, time, customer, barman):
        super().__init__(time)
        self.customer = customer
        self.barman = barman

    def handle(self, simulation):
        """
        Handles the departure of a customer from the bar.
        """
        # שחרור הברמן
        self.barman.setBarmanStatus(False)
        print(f"Barman {self.barman} finished serving Customer {self.customer.customerId} at time {self.time}.")

        # אם יש אנשים בתור
        bar = simulation.Hotel.getFacility("bar")
        if bar.barQueue:
            # הוצאת הלקוח הבא מהתור
            next_customer = bar.barQueue.pop(0)

            # התחלת שירות ללקוח הבא עם הברמן הפנוי
            self.barman.setBarmanStatus(True)
            print(f"Customer {next_customer.customerId} started bar service with {self.barman} at time {self.time}.")

            # חישוב זמן השירות ללקוח הבא
            service_time = self.time + sampleBarService()

            # תזמון אירוע עזיבה עבור הלקוח הבא
            simulation.scheduleEvent(BarDepartureEvent(service_time, next_customer, self.barman))


class SpaDepartureEvent(Event):
    def __init__(self, time, customer):
        super().__init__(time)
        self.customer = customer

    def handle(self, simulation):
        facility = simulation.hotel.getFacility("spa")

        facility.endCustomerActivity(self.customer)
        print(f"Customer {self.customer.customerId} left the spa at time {self.time}.")

        if facility.hasQueue():
            # הוצאת הלקוח הבא מהתור ומחיקתו
            next_customer = facility.queue.pop(0)  # הלקוח הראשון בתור

            # עדכון הפעילות ביומן של הלקוח
            next_customer.daily_activities["spa"][0] = True
            next_customer.daily_activities["spa"][1] += 1

            # חישוב זמן השירות ללקוח הבא
            service_time = self.time + sampleSpa()

            # הכנסת הלקוח לפעילות
            facility.addCustomerToActivity(next_customer)
            print(f"Customer {next_customer.customerId} started spa activity at time {self.time}.")

            # תזמון אירוע עזיבת הספא עבור הלקוח הבא
            simulation.scheduleEvent(SpaDepartureEvent(service_time, next_customer))






class RenegingEvent(Event):
    def __init__(self, time, customer,activity_queues):
        super().__init__(time)
        self.customer = customer
        self.activity_queues = activity_queues

    def handle(self, simulation):
        """
        טיפול באירוע Reneging:
        1. מחיקת הלקוח מהתור הנוכחי.
        2. תזמון הפעילות הבאה לפי המילון של הלקוח.
        """

        if self.customer in self.activity_queues:
            # מחיקת הלקוח מהתור הנוכחי
            self.activity_queues.remove(self.customer)
        print(f"Handling RenegingEvent for Customer {self.customer.customerId} at time {self.time}.")

        # מציאת הפעילות הבאה ביומן
        next_activity = None
        for activity, status in self.customer.daily_activities.items():
            if not status[0] and status[1] == 0:  # הפעילות לא בוצעה בכלל
                next_activity = activity
                break

            # אם כל הפעילויות כבר בוצעו פעם אחת, מחפשים פעילות עם פחות משני ניסיונות
        if next_activity is None:
            for activity, status in self.customer.daily_activities.items():
                if status[1] < 2:  # הפעילות בוצעה פחות משני ניסיונות
                    next_activity = activity
                    break


        # אם יש פעילות הבאה
        if next_activity:
            # סימון הפעילות ביומן
            self.customer.daily_activities[next_activity][0] = True

            # תזמון האירוע הבא
            if next_activity == "pool":
                simulation.scheduleEvent(PoolEvent(self.time, self.customer))
            elif next_activity == "bar":
                simulation.scheduleEvent(BarEvent(self.time, self.customer))
            elif next_activity == "spa":
                simulation.scheduleEvent(SpaEvent(self.time, self.customer))
            else:
                print(f"Unknown activity: {next_activity}")
        else:
            print(f"Customer {self.customer.customerId} has completed all activities for the day.")



