from app import ma
from marshmallow import decorators


# Portfolio Schema
class PortfolioSchema(ma.Schema):

    class Meta:
        fields = ('id', 'customer_id', 'shares_bought')

    @decorators.post_dump(pass_many=True)
    def add_envelope(self, data, many, **kwargs):
        if many:
            for d in data:
                try:
                    d['shares_bought'] = [sh[0] for sh in d['shares_bought']]
                except TypeError:
                    d['shares_bought'] = [sh for sh in d['shares_bought']]
        else:
            try:
                data['shares_bought'] = [sh[0] for sh in data['shares_bought']]
            except TypeError:
                data['shares_bought'] = [sh for sh in data['shares_bought']]
        return data


# Init Schema
portfolio_schema = PortfolioSchema()
portfolios_schema = PortfolioSchema(many=True)
