NATIVE_TRANSFER_FEE = 0.0001
MINIMUM_SMARTTX_FEE = 0.0002
NON_NATIVE_TRANSFER_FEE = NATIVE_TRANSFER_FEE + MINIMUM_SMARTTX_FEE

def calc_supply_in(curr_supply, curr_reserve, reserve_in, reserve_ratio):
  return curr_supply * ((((reserve_in/curr_reserve) + 1)**(reserve_ratio)) - 1)
  
def calc_reserve_out(curr_reserve, curr_supply, supply_in, reserve_ratio):
  return curr_reserve * (1 - (1 - (supply_in/curr_supply))**(1/reserve_ratio))

def calc_price_in_reserve(reserve, supply, ratio):
  return reserve/(supply*ratio)

def calc_conversion_fees(amount_in):
  return amount_in * 0.00025

class Currency:
  def __init__(self, supply, reserves, r_ratio, start_price):
    self.supply = supply
    self.reserves = reserves
    self.r_ratio = r_ratio
    self.price = start_price
    self.total_fees = 0
    self.tx_fees = 0
    self.conversion_fees = 0
    
    self.cap_reserve_ratio()

  def update_price(self):
    self.price = calc_price_in_reserve(self.reserves, self.supply, self.r_ratio)
  
  def cap_reserve_ratio(self):
    self.r_ratio = self.r_ratio

    if self.r_ratio > 1:
      self.r_ratio = 1
  
  def reserve_to_supply(self, reserve_in):
    conversion_fee_percentage = calc_conversion_fees(reserve_in)
    conversion_fee = (conversion_fee_percentage if conversion_fee_percentage > MINIMUM_SMARTTX_FEE else MINIMUM_SMARTTX_FEE)
    
    fees_returned_to_reserve = conversion_fee / 2
    fees_paid_to_validators = (conversion_fee - fees_returned_to_reserve) + NATIVE_TRANSFER_FEE
    total_fees = fees_paid_to_validators + fees_returned_to_reserve

    self.total_fees = self.total_fees + total_fees
    self.conversion_fees = self.conversion_fees + conversion_fee
    self.tx_fees = self.tx_fees + NATIVE_TRANSFER_FEE
    
    conversion_amount = reserve_in - total_fees

    supply_output = calc_supply_in(self.supply, self.reserves, conversion_amount, self.r_ratio)
    
    self.supply = self.supply + supply_output
    self.reserves = (self.reserves + reserve_in + fees_returned_to_reserve) - fees_paid_to_validators
    self.update_price()

    return supply_output
    
  def supply_to_reserve(self, supply_in):
    conversion_fee_supply_currency = calc_conversion_fees(supply_in)
    conversion_fee_reserve_currency = calc_reserve_out(self.reserves, self.supply, conversion_fee_supply_currency, self.r_ratio)
    conversion_fee = (conversion_fee_reserve_currency if conversion_fee_reserve_currency > MINIMUM_SMARTTX_FEE else MINIMUM_SMARTTX_FEE)
    
    fees_returned_to_reserve = conversion_fee / 2
    fees_paid_to_validators = (conversion_fee - fees_returned_to_reserve) + NATIVE_TRANSFER_FEE
    total_fees = fees_paid_to_validators + fees_returned_to_reserve
    conversion_amount = supply_in

    reserve_output_amount = calc_reserve_out(self.reserves, self.supply, conversion_amount, self.r_ratio)

    self.reserves = (self.reserves + fees_returned_to_reserve) - (reserve_output_amount + fees_paid_to_validators)
    self.supply = self.supply - supply_in
    self.total_fees = self.total_fees + total_fees
    self.tx_fees = self.tx_fees + NATIVE_TRANSFER_FEE
    self.conversion_fees = self.conversion_fees + conversion_fee
    self.update_price()

    return reserve_output_amount - total_fees
  
  def prelaunch_carve_out(self, reserve_out):
    old_reserves = self.reserves

    self.reserves = self.reserves - reserve_out
    
    self.r_ratio = self.r_ratio * (self.reserves / old_reserves)
    self.cap_reserve_ratio()
    self.update_price()

    self.total_fees = self.total_fees + NATIVE_TRANSFER_FEE
    self.tx_fees = self.tx_fees + NATIVE_TRANSFER_FEE

    return reserve_out - NATIVE_TRANSFER_FEE
  
  def burn_change_price(self, supply_in):
    supply_burned = supply_in

    smarttx_fee = MINIMUM_SMARTTX_FEE
    fees_returned_to_reserve = smarttx_fee / 2
    fees_paid_to_validators = (smarttx_fee - fees_returned_to_reserve) + NATIVE_TRANSFER_FEE
    total_fees = fees_returned_to_reserve + fees_paid_to_validators

    self.total_fees = self.total_fees + total_fees
    self.tx_fees = self.tx_fees + total_fees

    self.supply = self.supply - supply_burned
    self.reserves = (self.reserves + fees_returned_to_reserve) - fees_paid_to_validators

    self.update_price()
  
  def burn_change_weight(self, supply_in):
    old_supply = self.supply

    supply_burned = supply_in

    smarttx_fee = MINIMUM_SMARTTX_FEE
    fees_returned_to_reserve = smarttx_fee / 2
    fees_paid_to_validators = (smarttx_fee - fees_returned_to_reserve) + NATIVE_TRANSFER_FEE
    total_fees = fees_returned_to_reserve + fees_paid_to_validators

    self.total_fees = self.total_fees + total_fees
    self.tx_fees = self.tx_fees + total_fees

    self.supply = self.supply - supply_burned
    self.reserves = (self.reserves + fees_returned_to_reserve) - fees_paid_to_validators

    self.r_ratio = self.r_ratio * (old_supply / self.supply)
    self.cap_reserve_ratio()
    self.update_price()
    
  def mint_change_weight(self, supply_out):
    old_supply = self.supply

    smarttx_fee = MINIMUM_SMARTTX_FEE
    fees_returned_to_reserve = smarttx_fee / 2
    fees_paid_to_validators = (smarttx_fee - fees_returned_to_reserve) + NATIVE_TRANSFER_FEE
    total_fees = fees_returned_to_reserve + fees_paid_to_validators

    self.total_fees = self.total_fees + total_fees
    self.tx_fees = self.tx_fees + total_fees

    self.supply = self.supply + supply_out
    self.reserves = (self.reserves + fees_returned_to_reserve) - fees_paid_to_validators

    self.r_ratio = self.r_ratio * (old_supply / self.supply)
    self.cap_reserve_ratio()
    self.update_price()

    return supply_out