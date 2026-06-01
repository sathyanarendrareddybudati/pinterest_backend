import numpy as np
from typing import List
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares
from app.models.models import Save, PinView
from sqlalchemy.orm import Session

class RecommendationEngine:
    def __init__(self):
        self.model = AlternatingLeastSquares(factors=50, regularization=0.1, iterations=20)
        self.user_items = None
        self.user_mapping = {}
        self.item_mapping = {}
        self.reverse_item_mapping = {}
        
    def _map_ids(self, user_uuid, pin_uuid, weight, rows, cols, data):
        if user_uuid not in self.user_mapping:
            self.user_mapping[user_uuid] = len(self.user_mapping)
        if pin_uuid not in self.item_mapping:
            item_idx = len(self.item_mapping)
            self.item_mapping[pin_uuid] = item_idx
            self.reverse_item_mapping[item_idx] = pin_uuid
            
        rows.append(self.user_mapping[user_uuid])
        cols.append(self.item_mapping[pin_uuid])
        data.append(weight)

    def train(self, db: Session):
        """
        Train the collaborative filtering model using saves & pin views.
        """
        saves = db.query(Save).all()
        views = db.query(PinView).all()
        
        if not saves and not views:
            return
            
        rows, cols, data = [], [], []

        for save in saves:
            self._map_ids(save.user_id, save.pin_id, 3.0, rows, cols, data)
            
        for view in views:
            if view.user_id:
                self._map_ids(view.user_id, view.pin_id, 1.0, rows, cols, data)
            
        self.user_items = csr_matrix((data, (rows, cols)))
        self.model.fit(self.user_items)
        
    def recommend(self, user_id, num_items: int = 10):
        """
        Recommend pins for a given user UUID.
        """
        if self.user_items is None or user_id not in self.user_mapping:
            return []
            
        user_idx = self.user_mapping[user_id]
        recommendations, scores = self.model.recommend(user_idx, self.user_items[user_idx], N=num_items)
        
        pin_ids = [self.reverse_item_mapping[idx] for idx in recommendations]
        return pin_ids

recommender = RecommendationEngine()
