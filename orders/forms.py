from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    text = forms.CharField(
        required=False, max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4, "maxlength": 2000}),
    )

    class Meta:
        model = Review
        fields = ("rating", "text")
        labels = {"rating": "Оценка", "text": "Комментарий"}
        widgets = {
            "rating": forms.Select(choices=[(value, f"{value} из 5") for value in range(5, 0, -1)]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
