from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
import random


# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)


# Customer Class/Model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)

    def __init__(self, username):
        self.username = username


# Share Class/Model
class Share(db.Model):
    __tablename__ = 'shares'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'))
    rate = db.Column(db.Float, nullable=False)
    symbol = db.Column(db.String(3), unique=True, nullable=False)

    def __init__(self, customer_id, rate, symbol):
        self.customer_id = customer_id
        self.rate = rate
        self.symbol = symbol


# Portfolio Class/Model
class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    shares_bought = db.Column(db.PickleType, nullable=True)

    def __init__(self, customer_id, shares_bought):
        self.customer_id = customer_id
        self.shares_bought = shares_bought

# Get All Shares
@app.route('/api/shares', methods=['GET'])
def get_shares():
    from share.schemas import shares_schema

    all_shares = Share.query.all()
    return jsonify(shares_schema.dump(all_shares))


# Sell Share
@app.route('/api/sell', methods=['PUT'])
def sell():
    from share.schemas import share_schema

    share = Share.query.filter_by(id=int(request.json['share_id'])).first()
    portfolio = Portfolio.query.filter_by(customer_id=share.customer_id).first()
    if not portfolio:
        response = {'error': 'Portfolio does not exist.'}
        return jsonify(response), 404

    shares_bought = []
    if len(portfolio.shares_bought) > 0:
        try:
            shares_bought = [sh[0] for sh in portfolio.shares_bought]
        except TypeError:
            shares_bought = [sh for sh in portfolio.shares_bought]
    if share.id not in shares_bought:
        response = {'error': 'Share ({}) could not be found in portfolio.'.format(share.symbol)}
        return jsonify(response), 404
    # removes share from portfolio
    portfolio.shares_bought = [sh for sh in shares_bought if sh != share.id]
    # adds share to the new customer and its portfolio
    share.customer_id = request.json['customer_id']
    share.rate = request.json['rate']
    curr_portfolio = Portfolio.query.filter_by(customer_id=int(request.json['customer_id'])).first()
    try:
        curr_portfolio.shares_bought = [sh[0] for sh in curr_portfolio.shares_bought] + [share.id]
    except TypeError:
        curr_portfolio.shares_bought = [sh for sh in curr_portfolio.shares_bought] + [share.id]
    share.portfolio_id = curr_portfolio.id

    db.session.commit()

    return share_schema.jsonify(share)

# Buy Share
@app.route('/api/buy', methods=['PUT'])
def buy():
    from share.schemas import share_schema

    share = Share.query.filter_by(id=int(request.json['share_id'])).first()
    if share.customer_id == request.json['customer_id']:
        response = {'error': 'Share already belongs to this customer.'}
        return jsonify(response), 422
    previous_portfolio = Portfolio.query.filter_by(id=share.portfolio_id).first()
    if not share:
        response = {'error': 'Share does not exist.'}
        return jsonify(response), 404
    portfolio = Portfolio.query.filter_by(customer_id=request.json['customer_id']).first()
    if not portfolio:
        response = {'error': 'Portfolio does not exist.'}
        return jsonify(response), 404

    # buys new share and updates portfolio and customer
    share.customer_id = request.json['customer_id']
    share.portfolio_id = portfolio.id
    share.rate = request.json['rate']

    try:
        portfolio.shares_bought = [sh[0] for sh in portfolio.shares_bought] + [share.id]
    except TypeError:
        portfolio.shares_bought = [sh for sh in portfolio.shares_bought] + [share.id]

    # updates share's previous portfolio
    try:
        previous_portfolio.shares_bought = [sh[0] for sh in previous_portfolio.shares_bought if sh[0] != share.id]
    except TypeError:
        previous_portfolio.shares_bought = [sh for sh in previous_portfolio.shares_bought if sh != share.id]

    db.session.commit()

    return share_schema.jsonify(share)


# Get All Customers
@app.route('/api/customers', methods=['GET'])
def get_customers():
    from customer.schemas import customers_schema

    all_customers = Customer.query.all()
    return jsonify(customers_schema.dump(all_customers))


# Get All Portfolios
@app.route('/api/portfolios', methods=['GET'])
def get_portfolios():
    from portfolio.schemas import portfolios_schema

    all_portfolios = Portfolio.query.all()
    return jsonify(portfolios_schema.dump(all_portfolios))


def init_db():
    db.create_all()

    # Create 5 customers
    if db.session.query(Customer).filter(Customer.username.in_(["user001", "user002", "user003", "user004", "user005"])).count() < 1:
        customers = [Customer(username="user001"),
                     Customer(username="user002"),
                     Customer(username="user003"),
                     Customer(username="user004"),
                     Customer(username="user005")]
        db.session.add_all(customers)
        db.session.commit()

    # Create number of Shares for each Customer
    customer_ids = [cus.id for cus in Customer.query.all()]
    symbols = ['ABC', 'OPT', 'PTR', 'RPT', 'WER', 'CVB', 'MKN', 'FGR',
               'JBC', 'YPT', 'PIR', 'QPT', 'WTR', 'CAB', 'MKL']

    data = []
    if db.session.query(Share).filter(Share.customer_id.in_(customer_ids)).count() < 1:
        for customer_id in customer_ids:
            symbol1 = random.choice(symbols)
            params = {
                'customer_id': customer_id,
                'rate': float("{0:.2f}".format(random.uniform(10, 500))),
                'symbol': symbol1
            }
            data.append(params)
            symbols = [sym for sym in symbols if sym != symbol1]

            symbol2 = random.choice(symbols)
            params = {
                'customer_id': customer_id,
                'rate': float("{0:.2f}".format(random.uniform(10, 500))),
                'symbol': symbol2
            }
            data.append(params)
            symbols = [sym for sym in symbols if sym != symbol2]

            symbol3 = random.choice(symbols)
            params = {
                'customer_id': customer_id,
                'rate': float("{0:.2f}".format(random.uniform(10, 500))),
                'symbol': symbol3
            }
            data.append(params)
            symbols = [sym for sym in symbols if sym != symbol3]

        db.engine.execute(Share.__table__.insert(), data)

    # Create portfolios for each customer
    customer_ids = [cus.id for cus in Customer.query.all()]
    if db.session.query(Portfolio).filter(Portfolio.customer_id.in_(customer_ids)).count() < 1:
        portfolios = []
        for cus in customer_ids:
            share = Share.query.filter_by(customer_id=cus).with_entities(Share.id).all()
            portfolios.append(Portfolio(customer_id=cus, shares_bought=share))

        db.session.add_all(portfolios)

        for cus in customer_ids:
            Share.query.filter_by(customer_id=cus) \
                .update({Share.portfolio_id: Portfolio.query.filter_by(customer_id=cus).with_entities(Portfolio.id).first()[0]}, synchronize_session='fetch')

        db.session.commit()


# Run Server
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
