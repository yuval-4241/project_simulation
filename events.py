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


class closeHotelDayEvent(Event):
        # open the hotel to guests at 00:00
    def handle(self, simulation):
        current_date = self.time // (24 * 60)  # מחלקים את הזמן הכולל למקטעי ימים
        print(f"The day is: {current_date} ")
        print(f"The day is dont go to breakfast: {current_date} ,{simulation.hotelSimulation.didnt_go_to_breakfast}")  # todo:delet
        print(f"The day is  go to breakfast: {current_date}, {simulation.hotelSimulation.go_to_breakfast}")
        print(f"The day is  do checkout: {current_date} ,{simulation.hotelSimulation.do_today_checkout}")
        total_occupied_rooms = 110 - simulation.hotelSimulation.count_free_rooms()
        print(f"total rooms that occupaid ,{current_date} {total_occupied_rooms}")  # todo:delete
        simulation.hotelSimulation.didnt_go_to_breakfast = 0
        simulation.hotelSimulation.go_to_breakfast = 0
        simulation.hotelSimulation.do_today_checkout=0

        available_rooms=simulation.hotelSimulation.count_free_rooms()
        available_rooms_nextday = simulation.hotelSimulation.calculateAvailableRoomsByTypeAtMidnight(current_date)
        simulation.hotelSimulation.update_daily_rank()
        simulation.hotelSimulation.update_wait_total_for_Rank()
        current_lamda= simulation.hotelSimulation.calculate_lambda(available_rooms)
        simulation.scheduleEvent(closeHotelDayEvent(self.time + 24 * 60))



class CloseCustomerArrivalEvent(Event):  # close the hotel to guests at 5pm
    def handle(self, simulation):
        simulation.hotelSimulation.setPublicAccess(False)
        simulation.scheduleEvent(OpenHotelEvent(self.time + 15 * 60))  # schedule reopening at 8am




class CheckInArrivalEvent(Event):
    def handle(self, simulation):
        # יצירת הזמנה חדשה והוספתה לתור הלובי
        next_arrival_time = self.time + sampleCustomerArrival(simulation.hotelSimulation.get_hotal_lambda())  # חישוב זמן ההגעה הבא
        arrival_end_time = 17 * 60  # סיום ההגעה ב-17:00
        if next_arrival_time < simulation.simulationTime and self.time < arrival_end_time:
            simulation.scheduleEvent(CheckInArrivalEvent(next_arrival_time))

        booking = Booking(arrivalTime=self.time)
        if simulation.hotelSimulation.check_and_assign_room(booking):
            simulation.hotelSimulation.total_guest_groups+=1
            heapq.heappush(simulation.hotelSimulation.lobby_queue, booking)
            print(f"Booking {booking.bookingId} added to lobby queue at time {self.time}.")

        # תזמון ההגעה הבאה אם יש זמן נוסף בסימולציה

            day_start_time = (self.time // 1440) * 1440  # תחילת היום במונחי דקות

            # טווח השעות 15:00–20:00
            check_in_window_start = day_start_time + 900  # 15:00
            check_in_window_end = day_start_time + 1200  # 20:00

            # דגימת זמן השירות מההתפלגות
            service_time = sampleCheckIn()  # פונקציה שמחזירה זמן מבוסס על התפלגות דגימה
            check_in_start_time = check_in_window_start + service_time


            simulation.scheduleEvent(CheckInDepartureEvent(check_in_start_time, booking,))
        else:
            simulation.hotelSimulation.nothaveroom+=1

class CheckInDepartureEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking


    def handle(self, simulation):
        if simulation.hotelSimulation.lobby_queue:
            simulation.hotelSimulation.count_pepole_checkin+=1
            new_booking= heapq.heappop(simulation.hotelSimulation.lobby_queue)
            wait_time=self.time-new_booking.arrivalTime
            simulation.hotelSimulation.total_wait_forthisday.append(wait_time)
            start_day = int(self.booking.arrivalTime // 1440) + 1  # מתחילים מיום שלאחר יום ההגעה
            end_day = int(self.booking.arrivalTime // 1440 + self.booking.stayDuration)  # היום האחרון של השהייה

            for day in range(start_day, end_day):
                # חישוב זמן ארוחת הבוקר עבור כל יום
                breakfast_time = day * 1440 + (6.5 * 60) + sampleBreakfastTime()

                # תזמון האירוע
                simulation.scheduleEvent(BreakfastArrivalEvent(breakfast_time, self.booking))

            # תזמון צ'ק-אאוט ביום האחרון בשעה 11:00
            checkout_time = (int(self.booking.arrivalTime // 1440) + self.booking.stayDuration - 1) * 1440 + 11 * 60
            simulation.scheduleEvent(CheckOutReminderEvent(checkout_time, self.booking))

class CheckoutArrivleEvent(Event):
    def __init__(self, time, booking):
        super().__init__(time)
        self.booking = booking

    def handle(self, simulation):
        """
        Handle the checkout event for the group.
        """
        server = simulation.hotelSimulation.find_available_server()
        if server is not None:
            simulation.hotelSimulation.assign_to_server(self.time, server, self.booking)
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
        # Provide feedback and release the room
        feedback = random.randint(1, 10)
        simulation.hotelSimulation.rank_feedback.append(feedback)
        simulation.hotelSimulation.release_room(self.booking)
        simulation.hotelSimulation.do_today_checkout += 1
        print(f"Room released for booking {self.booking.bookingId}")

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
        self.booking=booking

    def handle(self, simulation):

        breakfast_start_time = 6.5 * 60  # שעה 6:30 במונחי דקות
        breakfast_end_time = 11 * 60    # שעה 11:00 במונחי דקות
        local_time = self.time % 1440
        # בדיקה אם הזמן הוא במסגרת שעות פעילות חדר האוכל
        if not (breakfast_start_time <= local_time< breakfast_end_time):
            simulation.hotelSimulation.didnt_go_to_breakfast+=1
            return  # אם חדר האוכל סגור, האירוע לא מבוצע


        available_table_index = simulation.hotelSimulation.find_available_table()
        if available_table_index is not None:
            # סימון השולחן כתפוס
            simulation.hotelSimulation.tables[available_table_index].set_status(True)
            print(f"Table seat {self.booking.bookingId} at table {available_table_index}")
            breakfast_duration =self.time+ sampleBreakfastTime()
            simulation.scheduleEvent(BreakfastDepartureEvent( breakfast_duration,self.booking, available_table_index))
            if self.booking.isLastDay(self.time):
                simulation.hotelSimulation.count_pepole_brekfast_checkout += 1
                simulation.scheduleEvent(CheckoutArrivleEvent(breakfast_duration, self.booking))
        else:
            self.booking.breakfastArrivalTime = self.time
            simulation.hotelSimulation.breakfast_queue.append(self.booking)

class BreakfastDepartureEvent(Event):
    def __init__(self, time, booking, table_index):
        super().__init__(time)
        self.booking = booking
        self.table_index = table_index

    def handle(self, simulation):
        # בדיקה אם יש לקוחות בתור
        simulation.hotelSimulation.go_to_breakfast+=1
        if simulation.hotelSimulation.breakfast_queue:
            # הושבת הלקוח הראשון בתור
            next_booking = simulation.hotelSimulation.breakfast_queue.pop(0)
            print(f"Booking {next_booking.bookingId} seated at table {self.table_index} from queue.")

            # סימון זמן ההמתנה
            waiting_time = self.time - next_booking.breakfastArrivalTime
            simulation.hotelSimulation.total_wait_forthisday.append(waiting_time)

            # תזמון עזיבה חדשה ללקוח מהתור
            breakfast_duration = sampleBreakfastTime()
            simulation.scheduleEvent(BreakfastDepartureEvent(self.time + breakfast_duration, next_booking, self.table_index))


        if self.booking.isLastDay(self.time) and not self.booking.hasCheckedOut:
            simulation.scheduleEvent(CheckoutArrivleEvent(self.time, self.booking))
            self.booking.hasCheckedOut = True
        else:
            # סימון השולחן כפנוי
            simulation.hotelSimulation.tables[self.table_index].set_status(False)
            print(f"Table {self.table_index} is now available.")

        # ספירת אנשים שסיימו ארוחת בוקר
        simulation.hotelSimulation.count_pepole_brekfast_done += 1
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
            print(f"Booking {self.booking.bookingId} missed breakfast, going to checkout.")
            simulation.scheduleEvent(CheckoutArrivleEvent(self.time, self.booking))
            self.booking.hasCheckedOut = True
