class StockAnalytics:
    @staticmethod
    def calculate_roi(cost, market_value):
        if cost == 0: return 0
        return ((market_value - cost) / cost) * 100

    @staticmethod
    def calculate_profit(cost, market_value):
        return market_value - cost

    @staticmethod
    def get_best_performer(positions):
        if not positions: return None
        return max(positions, key=lambda x: x['roi'])

    @staticmethod
    def get_worst_performer(positions):
        if not positions: return None
        return min(positions, key=lambda x: x['roi'])

    @staticmethod
    def get_largest_weight(positions):
        if not positions: return None
        return max(positions, key=lambda x: x['market_value'])