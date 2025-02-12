import json


import os
from glob import glob
from datetime import datetime
import logging

class WhaleTracker:
    def __init__(self):
        self.clean_data_dir = 'data/clean'
        
    def get_historical_files(self):
        """Get list of clean data files sorted by timestamp"""
        files = glob(os.path.join(self.clean_data_dir, 'data_*.json'))
        return sorted(files)

    def analyze_whale_activity(self, threshold_usd=10000):
        """
        Analyze whale activity by looking at large purchases before price increases
        
        Args:
            threshold_usd: Minimum USD value to consider as whale activity
        """
        files = self.get_historical_files()
        if not files:
            logging.error("No clean data files found")
            return []

        whale_activities = []
        
        for i in range(len(files)-1):
            # Load consecutive files to compare
            with open(files[i], 'r') as f1, open(files[i+1], 'r') as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)
                
                # Get timestamp from filename
                timestamp = files[i].split('data_')[1].split('.json')[0]
                
                # Compare each token's data
                for token1, token2 in zip(data1, data2):
                    # Calculate volume in USD
                    volume_usd = float(token1['volume']['h1']) * float(token1['current_price']['usd'])
                    
                    # Check if there were large buys (volume > threshold)
                    if volume_usd > threshold_usd:
                        # Calculate price increase
                        price1 = float(token1['current_price']['usd'])
                        price2 = float(token2['current_price']['usd'])
                        price_change = ((price2 - price1) / price1) * 100
                        
                        # If price increased significantly after large buys
                        if price_change > 10:  # 10% threshold
                            whale_activity = {
                                'timestamp': timestamp,
                                'token_address': token1['token_address'],
                                'network': token1['network'],
                                'volume_usd': volume_usd,
                                'buy_price': price1,
                                'current_price': price2,
                                'price_increase': price_change,
                                'transaction_count': token1['transactions']['h1']['buys']
                            }
                            whale_activities.append(whale_activity)
        
        return whale_activities

    def get_current_whale_holdings(self):
        """Get current holdings of identified whale addresses"""
        files = self.get_historical_files()
        if not files:
            return []
            
        # Get most recent file
        latest_file = files[-1]
        with open(latest_file, 'r') as f:
            current_data = json.load(f)
            
        whale_holdings = []
        for token in current_data:
            # Look at large holders based on transaction volume
            volume_usd = float(token['volume']['h24']) * float(token['current_price']['usd'])
            if volume_usd > 10000:  # Threshold for whale activity
                holding = {
                    'token_address': token['token_address'],
                    'network': token['network'],
                    'holding_value_usd': volume_usd,
                    'current_price': token['current_price']['usd'],
                    'market_cap': token['market_cap'],
                    'liquidity': token['liquidity']['usd']
                }
                whale_holdings.append(holding)
                
        return whale_holdings


