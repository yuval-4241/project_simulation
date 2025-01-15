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
        print(f"The total rooms occipud for the end of the day  : {current_date } is: {110-available_rooms}")
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



class FirstDayPool(Event): #todo:delete
    def __init__(self, time,booking):
        super().__init__(time)
        self.booking = booking


    def handle(self, simulation):
        local_time=self.time%1440
        if local_time<19*60:
            return
            if simulation.check_pool_availability(booking):

