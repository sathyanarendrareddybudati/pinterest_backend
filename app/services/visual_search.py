import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import io

class VisualSearchService:
    def __init__(self):
        self.model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        self.model = torch.nn.Sequential(*(list(self.model.children())[:-1]))
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225]),
        ])

    def encode_image(self, image_bytes: bytes) -> list:
        """
        Generate a feature embedding for an image using ResNet50.
        Returns a list of floats (vector).
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_t = self.transform(image)
        batch_t = torch.unsqueeze(img_t, 0)
        
        with torch.no_grad():
            out = self.model(batch_t)
            
        embedding = out.flatten().tolist()
        return embedding

visual_search = VisualSearchService()