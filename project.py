from fundraiser import Fundraiser

# Investments received during the lock period will be locked for lock length, at which point
# revenue begins to flow in, causing steady burn

class Project:
  def __init__(self, target_ratio, std, initial_reserve, target_threshold):
    self.fundraiser = Fundraiser(target_ratio, std, initial_reserve, target_threshold)
    self.block = 1

    self.invested_reserve = 0
    self.reserve_returns = 0
    self.invested_fractional = 0
    self.revenues_reserve = 0

    self.total_fractional_raised = 0
    self.total_reserve_raised = 0

    self.start_price = self.fundraiser.currency.price

    self.budget_deficit = 0

    self.investments_fractional_last_block = 0
  
  def advance_block(self, investment_in_reserve, investment_out_supply, revenues_reserve, reserve_income_required, is_prelaunch):
    if investment_in_reserve > 0:
      self.investments_fractional_last_block = self.fundraiser.invest(investment_in_reserve)
    else:
      self.investments_fractional_last_block = 0

    self.invested_reserve = self.invested_reserve + investment_in_reserve
    self.invested_fractional = self.invested_fractional + self.investments_fractional_last_block

    self.invested_fractional = self.invested_fractional - investment_out_supply

    if investment_out_supply > 0:
      self.reserve_returns = self.reserve_returns + self.fundraiser.divest(investment_out_supply)

    self.revenues_reserve = self.revenues_reserve + revenues_reserve

    if revenues_reserve > 0:
      self.fundraiser.accept_revenue(revenues_reserve)

    self.budget_deficit = self.budget_deficit + reserve_income_required

    funds_available = 0

    if self.budget_deficit > 0:
      if is_prelaunch:
        reserve_raised = self.fundraiser.currency.prelaunch_carve_out(self.budget_deficit)
        self.budget_deficit = self.budget_deficit - reserve_raised
        self.total_reserve_raised = self.total_reserve_raised + reserve_raised
      else:
        mintable_currency = self.fundraiser.get_mintable()
        est_mint_needed = self.budget_deficit/self.fundraiser.currency.price

        if est_mint_needed > mintable_currency:
          funds_available = funds_available + self.fundraiser.currency.mint_change_weight(mintable_currency)
        else:
          funds_available = funds_available + self.fundraiser.currency.mint_change_weight(est_mint_needed)

    if funds_available > 0:
      self.total_fractional_raised = self.total_fractional_raised + funds_available
      reserve_raised = self.fundraiser.divest(funds_available)
      self.total_reserve_raised = self.total_reserve_raised + reserve_raised
      self.budget_deficit = self.budget_deficit - reserve_raised
    
    self.block = self.block + 1
  
  def estimate_roi(self):
    return self.fundraiser.currency.price / self.start_price
    
    