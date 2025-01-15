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
        simulation.hotelSimulation.setPublicAccess(True)
        simulation.scheduleEvent(CloseCustomerArrivalEvent(self.time + 9 * 60))
        next_arrival_time = self.time + sampleCustomerArrival(simulation.hotelSimulation.get_hotal_lambda())
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


        available_rooms=simulation.hotelSimulation.count_free_rooms()
        print(f"The total rooms for the end of the day  : {current_date } is: {110-available_rooms}")
        available_rooms_nextday = simulation.hotelSimulation.calculateAvailableRoomsByTypeAtMidnight(current_date+1)
        simulation.hotelSimulation.update_daily_rank()
        current_lamda= simulation.hotelSimulation.calculate_lambda(available_rooms)
        print(f"The lamda for tomorow is   : {current_date+1} and lamda is: {current_lamda}")
        simulation.scheduleEvent(closeHotelDayEvent(self.time + 24 * 60))
        simulation.hotelSimulation.group_checked_out = 0
        simulation.hotelSimulation.count_pepole_NObrekfast_checkout = 0
        simulation.hotelSimulation.count_pepole_checkout_after_breakfast = 0
        simulation.hotelSimulation.didnt_go_to_breakfast = 0
        simulation.hotelSimulation.go_to_breakfast = 0


class CloseCustomerArrivalEvent(Event):  # close the hotel to guests at 5pm
    def handle(self, simulation):
        simulation.hotelSimulation.setPublicAccess(False)
        current_date = self.time // (24 * 60) +1 # מחלקים את הזמן הכולל למקטעי ימים
        simulation.scheduleEvent(OpenHotelEvent(self.time + 15 * 60))  # schedule reopening at 8am




class CheckInArrivalEvent(Event):
    def handle(self, simulation):
        # יצירת הזמנה חדשה והוספתה לתור הלובי
        next_arrival_time = self.time + sampleCustomerArrival(simulation.hotelSimulation.get_hotal_lambda())
        local_time = next_arrival_time % 1440  # השעה הנוכחית במונחי דקות ביום

        # בדיקה אם השעה היא בין 08:00 ל-17:00
        check_in_start_time = 8 * 60  # 08:00 במונחי דקות
        check_in_end_time = 17 * 60  # 17:00 במונחי דקות

        if  (check_in_start_time <= local_time < check_in_end_time):
        # חישוב זמן ההגעה הבא
            simulation.scheduleEvent(CheckInArrivalEvent(next_arrival_time))

        booking = Booking(next_arrival_time)
        if simulation.hotelSimulation.check_and_assign_room(booking):
            simulation.hotelSimulation.total_guest_groups+=1
            heapq.heappush(simulation.hotelSimulation.lobby_queue, booking)
            print(f"Booking {booking.bookingId} added to lobby queue at time {self.time}.")

        # תזמון ההגעה הבאה אם יש זמן נוסף בסימולציה

        else:
            simulation.hotelSimulation.nothaveroom+=1

class CheckInDepartureEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        # בדיקה אם התור ריק
        if not simulation.hotelSimulation.lobby_queue:
            print(f"No guests in the lobby queue at time {self.time}.")
            return

        # שליפת האורח הראשון בתור
        next_booking = heapq.heappop(simulation.hotelSimulation.lobby_queue)
        service_time = sampleCheckIn()
        # חישוב הזמן הנוכחי ביום
        time_in_day = self.time % 1440+service_time
        # השעה הנוכחית במונחי דקות ביום

        # בדיקה אם השעה הנוכחית גדולה מ-20:00
        if time_in_day > 20 * 60:  # 20:00 במונחי דקות
            print(f"Time {self.time} exceeds 20:00. Guest {next_booking.bookingId} is skipped.")
            return

        # חישוב זמן השירות ותזמון האורח הבא

        simulation.scheduleEvent(CheckInDepartureEvent(time_in_day, next_booking))

        # עדכון מידע על האורח
        simulation.hotelSimulation.count_pepole_checkin += 1
        wait_time = self.time - next_booking.arrivalTime
        simulation.hotelSimulation.total_wait_forthisday.append(wait_time)

        # תזמון ארוחות בוקר לכל יום שהייה
        start_day = int(next_booking.arrivalTime // 1440+1)
        end_day = int(next_booking.arrivalTime // 1440 +1+ next_booking.stayDuration)

        for day in range(start_day, end_day+1):
            breakfast_time = day * 1440 + (6.5 * 60) + sampleBreakfastRate()
            simulation.scheduleEvent(BreakfastArrivalEvent(breakfast_time, next_booking))

        # תזמון צ'ק-אאוט ביום האחרון בשעה 11:00
        checkout_time = (start_day+1 + next_booking.stayDuration) * 1440 + 11 * 60
        simulation.scheduleEvent(CheckOutReminderEvent(checkout_time, next_booking))


class CheckoutArrivleEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        """
        Handle the checkout event for the group.

        """
        feedback = random.randint(1, 10)
        simulation.hotelSimulation.rank_feedback.append(feedback)
        server = simulation.hotelSimulation.find_available_server()
        if server is not None:

            simulation.hotelSimulation.assign_to_server( server)
            service_time = self.time + sampleCheckOut()
            simulation.scheduleEvent(CheckOutDepartureEvent(service_time, server, self.booking))
        else:
            # Add to the priority queue (negative priority for max-heap behavior)
            simulation.hotelSimulation.check_out_queue.append((self.time, self.booking))


class CheckOutDepartureEvent(Event):  # Add inheritance from Event
    def __init__(self, time, server_id, booking):
        super().__init__(time)
        self.server_id = server_id
        self.booking = booking

    def handle(self, simulation):
        """
        Handle the departure event after checkout.
        """

        simulation.hotelSimulation.group_checked_out += 1
        # Mark the server as free or assign to the next booking in queue
        if simulation.hotelSimulation.check_out_queue:
            next_booking_time, next_booking = simulation.hotelSimulation.check_out_queue.pop(0)
            service_time = self.time + sampleCheckOut()
            simulation.scheduleEvent(CheckOutDepartureEvent(service_time, self.server_id, next_booking))
        else:
            simulation.hotelSimulation.server_states[self.server_id] = False



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
            simulation.hotelSimulation.didnt_go_to_breakfast += 1
            return

        available_table_index = simulation.hotelSimulation.find_available_table()
        if available_table_index is not None:

            breakfast_duration = self.time + sampleBreakfastTime()

            simulation.hotelSimulation.tables[available_table_index].set_status(True)
            print(f"Table seat {self.booking.bookingId} at table {available_table_index}")
            simulation.scheduleEvent(BreakfastDepartureEvent(breakfast_duration, self.booking, available_table_index))

        else:
            self.booking.breakfastArrivalTime = self.time
            simulation.hotelSimulation.breakfast_queue.append(self.booking)

class BreakfastDepartureEvent(Event):
    def __init__(self, time, booking, table_id):
        super().__init__(time)
        self.booking = booking
        self.table_id = table_id

    def handle(self, simulation):
                # שחרור השולחן

        simulation.hotelSimulation.go_to_breakfast += 1
        simulation.hotelSimulation.tables[self.table_id].set_status(False)
        print(f"Table {self.table_id} is now available.")


        # בדיקה אם זה היום האחרון של האורח ותזמון צ'ק-אאוט
        if self.booking.isLastDay(self.time // 1440 + 1) and not self.booking.hasCheckedOut:
            simulation.hotelSimulation.count_pepole_checkout_after_breakfast += 1
            self.booking.hasCheckedOut = True
            simulation.scheduleEvent(CheckoutArrivleEvent(self.time, self.booking))

        # אם יש אנשים בתור, הושב אותם לשולחן שהתפנה
        if simulation.hotelSimulation.breakfast_queue:
            next_booking = simulation.hotelSimulation.breakfast_queue.pop(0)
            print(f"Booking {next_booking.bookingId} seated at table {self.table_id} from queue.")
            breakfast_duration = self.time + sampleBreakfastTime()
            simulation.scheduleEvent(BreakfastDepartureEvent(breakfast_duration, next_booking, self.table_id))

        if random.random() < 0.1:  # 10% סיכוי
            print(f"Booking {self.booking.bookingId} did not enjoy the breakfast.")
            simulation.hotelSimulation.rate_for_breakfast=simulation.hotelSimulation.rate_for_breakfast+0.025  # השפעה שלילית על הדירוג


        # אם זה היום האחרון, תזמן צ'ק-אאוט


class CheckOutReminderEvent(Event):
    def __init__(self, time, booking):
       super().__init__(time)
       self.booking = booking

    def handle(self, simulation):
        # בדיקה אם האורח כבר ביצע צ'ק-אאוט
       if not self.booking.hasCheckedOut:
            simulation.hotelSimulation.count_pepole_NObrekfast_checkout += 1
            print(f"Booking {self.booking.bookingId} missed breakfast, going to checkout.")
            self.booking.hasCheckedOut = True
            simulation.scheduleEvent(CheckoutArrivleEvent(self.time, self.booking))



class calcbrefasteachday(Event): #todo:delete
    def __init__(self, time):
        super().__init__(time)


    def handle(self, simulation):
        current_date = self.time // (24 * 60)  # מחלקים את הזמן הכולל למקטעי ימים
        print(f"The day for pepole arrive at : {current_date} ")
        print(f"The day is dont go to breakfast: {current_date+1} ,{simulation.hotelSimulation.didnt_go_to_breakfast }")  # todo:delet
        print(f"The day is  go to breakfast: {current_date+1}, {simulation.hotelSimulation.go_to_breakfast}")
        simulation.scheduleEvent(calcbrefasteachday(self.time+24*60))



class calccheckout(Event): #todo:delete
    def __init__(self, time):
        super().__init__(time)


    def handle(self, simulation):
        current_date = self.time // (24 * 60) +1 # מחלקים את הזמן הכולל למקטעי ימים
        print(f"The total people did checkout  {simulation.hotelSimulation.group_checked_out} at day,{current_date} ")
        print(f"The total people did checkout NO BREAKFAST  {simulation.hotelSimulation.count_pepole_NObrekfast_checkout} at day,{current_date} ")
        print(f"The total people did checkout YES BREAKFAST {simulation.hotelSimulation.count_pepole_checkout_after_breakfast} at day,{current_date} ")
        simulation.scheduleEvent(calccheckout(self.time + 24 * 60))



