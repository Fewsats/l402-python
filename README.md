# l402-python


<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Usage

### Installation

Install latest from [pypi](https://pypi.org/project/l402/)

``` sh
$ pip install l402
```

### Documentation

Documentation can be found hosted on this GitHub
[repository](https://github.com/Fewsats/l402-python)’s
[pages](https://Fewsats.github.io/l402-python/). Additionally you can
find package manager specific guidelines on
[conda](https://anaconda.org/Fewsats/l402-python) and
[pypi](https://pypi.org/project/l402-python/) respectively.

## How to use

### Paying with the L402

The L402 supports multiple payment providers. In this example we’ll use
a coinbase wallet as an onchain provider. This wallet will be used to
pay for L402 offers.

``` python
from l402.payment_clients import Client, CoinbaseProvider
from cdp import Wallet
```

``` python
# CDP can be directly used as an onchain provider.
w = Wallet.create()

c = Client(onchain_provider=CoinbaseProvider(wallet=w))
```

Next we retrieve an offer from a demo server. This will return a 402
status code and a JSON response with the available offers.

``` python
r1 = httpx.get("http://localhost:9000/offers")
r1.status_code, r1.json()
```

    (402,
     {'offers': [{'amount': 1,
        'currency': 'USD',
        'description': 'Purchase 1 credit for API access',
        'offer_id': '58e1ee0a-e283-4f80-8a41-5c2f0ea138ca',
        'payment_methods': ['onchain'],
        'title': '1 Credit Package',
        'type': 'one-time'}],
      'payment_context_token': '42f46106-8989-4ed1-a770-adf9ad64c30b',
      'payment_request_url': 'http://localhost:9000/payment_request',
      'version': '0.2.2'})

To pay, we just need to provide the L402 response to the client and it
will automatically use configured payment provider that matches the
payment method.

``` python
if r1.status_code == HTTPStatus.PAYMENT_REQUIRED:
    ps = c.pay(r1.json())
```

### Getting paid with the L402

The L402 protocol implements a two-step payment flow:

1.  The server returns a `402 Payment Required` status code and
    information about the available offers.
2.  The client uses the L402 response to fetch the information for a
    specific payment method.

In this example, we implement this using a server with two endpoints:

1.  `/offers` - Returns available payment options with 402 status
2.  `/payment_request` - Generates payment details for chosen payment
    method

``` python
from l402.payment_providers import PaymentServer, Offer

app = FastAPI()


ps = PaymentServer(
    payment_request_url="http://localhost:9000/payment_request",
    onchain_provider=w,
)

@app.get("/offers")
def offers():
    offers_list = [Offer(
        amount=1,
        currency='USD',
        description='Purchase 1 credit for API access',
        offer_id=str(uuid4()),
        payment_methods=['onchain'],
        title='1 Credit Package',
        type='one-time'
    )]
    
    offers_response = ps.create_offers(offers_list)
    # Return the status code 402 Payment Required with the offers
    return JSONResponse(content=offers_response.model_dump(), status_code=402)

@app.post("/payment_request")
async def create_payment_request(request: PaymentRequest):
    payment_request = ps.create_payment_request(**request.model_dump())
    return JSONResponse(content=payment_request)
```

``` python
r = httpx.get("http://localhost:9000/offers")
offers_data = r.json()
r.status_code, offers_data
```

    (402,
     {'offers': [{'amount': 1,
        'currency': 'USD',
        'description': 'Purchase 1 credit for API access',
        'offer_id': '1808e12c-1824-49d8-a348-278959f6008d',
        'payment_methods': ['onchain'],
        'title': '1 Credit Package',
        'type': 'one-time'}],
      'payment_context_token': '82dbf89a-b18f-4737-b350-c58731b1cc18',
      'payment_request_url': 'http://localhost:9000/payment_request',
      'version': '0.2.2'})

The client can use this offer to request the information for a payment
method. We have to choose the payment method and, in the case of
coinbase, the chain and asset.

``` python
offers_data = dict2obj(offers_data)
data = {
    "offer_id": offers_data.offers[0].offer_id, 
    "payment_method": 'onchain',
    "chain": 'base-sepolia', # choose the chain where you want to pay
    "asset": 'usdc', # choose the asset you want to pay
    "payment_context_token": offers_data.payment_context_token 
}
r = httpx.post(offers_data.payment_request_url, json=data)
r, r.json()
```

    (<Response [200 OK]>,
     {'expires_at': '2025-01-30T21:03:46.502392+00:00',
      'offer_id': '1808e12c-1824-49d8-a348-278959f6008d',
      'payment_request': {'address': '0x6EC717D99534aF3917E25De1024f9e5BcDc1B262',
       'chain': 'base-sepolia',
       'asset': 'usdc'},
      'version': '0.2.2'})
