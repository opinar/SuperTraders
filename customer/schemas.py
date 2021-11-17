from app import ma


# Customer Schema
class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username')


# Init Schema
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
