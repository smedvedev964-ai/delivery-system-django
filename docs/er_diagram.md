# ER-диаграмма системы «Везём»

```mermaid
erDiagram
    USER ||--o| ADDRESS : "сохраняет"
    USER ||--o| CART : "имеет"
    CART ||--o{ CART_ITEM : "содержит"
    PRODUCT ||--o{ CART_ITEM : "добавлен"
    RESTAURANT ||--o{ PRODUCT : "предлагает"
    CATEGORY ||--o{ PRODUCT : "группирует"
    USER ||--o{ ORDER : "оформляет"
    ADDRESS ||--o{ ORDER : "снимок адреса"
    ORDER ||--|{ ORDER_ITEM : "содержит"
    PRODUCT ||--o{ ORDER_ITEM : "куплен как снимок"
    ORDER ||--o{ ORDER_STATUS_HISTORY : "аудируется"
    USER ||--o{ ORDER_STATUS_HISTORY : "меняет статус"
    USER ||--o| COURIER_PROFILE : "работает курьером"
    ORDER ||--o{ DELIVERY : "назначается"
    USER ||--o{ DELIVERY : "доставляет"
    USER ||--o{ DELIVERY : "назначает"
    ORDER ||--o| REVIEW : "оценивается"
    USER ||--o{ REVIEW : "оставляет"
    USER ||--o{ NOTIFICATION : "получает"
```

`OrderItem.unit_price` и `OrderItem.product_name` сохраняют данные на момент покупки. `Order.address_snapshot` хранит адрес отдельно от редактируемого адреса клиента. Один сохранённый адрес обеспечен связью OneToOne. Переназначения остаются в `Delivery`; актуальное назначение помечено `is_current`.
