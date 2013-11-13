from floppyforms.widgets import (
    DateInput as BaseDateInput, TimeInput as BaseTimeInput,
    SplitDateTimeWidget as BaseSplitDateTimeWidget)


class DateInput(BaseDateInput):
    template_name = 'floppyforms/date_widget.html'


class TimeInput(BaseTimeInput):
    template_name = 'floppyforms/time_widget.html'


class SplitDateTimeWidget(BaseSplitDateTimeWidget):
    def __init__(self, attrs=None, date_format=None, time_format=None):
        widgets = (DateInput(attrs=attrs, format=date_format),
                   TimeInput(attrs=attrs, format=time_format))
        super(BaseSplitDateTimeWidget, self).__init__(widgets, attrs)
