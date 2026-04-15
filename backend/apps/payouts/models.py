from django.db import models

class PayoutSchedule(models.Model):
    """
    Model to represent payout schedules for creators.
    """
    creator = models.ForeignKey(
        'creators.CreatorProfile', on_delete=models.CASCADE, related_name='payout_schedules')
    frequency = models.CharField(
        max_length=20, choices=[('weekly', 'Weekly'),
                                ('bi-weekly', 'Bi-Weekly'), ('monthly', 'Monthly')])
    next_payout_date = models.DateTimeField()

    
    def __str__(self):
        return f"{self.creator.user.username} - {self.frequency} payout schedule"

    @property
    def is_due_for_payout(self):
        """
        Check if the payout is due based on the next payout date.
        """
        from django.utils import timezone
        return timezone.now() >= self.next_payout_date


    def update_next_payout_date(self):
        """
        Update the next payout date based on the frequency.
        The next date should be the next wednesday for weekly,
        the next 1st and 15th for bi-weekly,
        and the next 1st of the month for monthly.
        """
        from django.utils import timezone
        from datetime import timedelta, datetime

        now = timezone.now()

        if self.frequency == 'weekly':
            # Set next payout date to the next Wednesday
            days_ahead = (2 - now.weekday() + 7) % 7  # 2 is Wednesday
            if days_ahead == 0:  # If today is Wednesday, set to next week
                days_ahead = 7
            self.next_payout_date = now + timedelta(days=days_ahead)

        elif self.frequency == 'bi-weekly':
            # Set next payout date to the next 1st or 15th
            if now.day < 15:
                self.next_payout_date = now.replace(day=15)
            else:
                # Move to the next month and set to the 1st
                next_month = (now.month % 12) + 1
                year = now.year + (now.month // 12)
                self.next_payout_date = now.replace(year=year, month=next_month, day=1)

        elif self.frequency == 'monthly':
            # Set next payout date to the next 1st of the month
            next_month = (now.month % 12) + 1
            year = now.year + (now.month // 12)
            self.next_payout_date = now.replace(year=year, month=next_month, day=1)

        self.save()
      