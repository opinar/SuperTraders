from app import ma


# Share Schema
class ShareSchema(ma.Schema):
    class Meta:
        fields = ('id', 'customer_id', 'portfolio_id', 'rate', 'symbol')


# Init Schema
share_schema = ShareSchema()
shares_schema = ShareSchema(many=True)
