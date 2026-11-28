from django import forms


class AnalyticsDateFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        label="Начало периода",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    end_date = forms.DateField(
        required=False,
        label="Конец периода",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and start > end:
            raise forms.ValidationError("Начало периода должно быть раньше его окончания.")
        return cleaned
