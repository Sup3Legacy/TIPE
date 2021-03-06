from __future__ import print_function, division
import os
import cv2
import csv
import torch
import pandas as pd
from skimage import io, transform
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import transforms, utils

ABSOLUTE = 'D:/Documents/Prepa/TIPE'

pathNormal = ABSOLUTE + "/Images/Normal/"
pathAltered = ABSOLUTE + "/Images/Altered/"
pathModels = ABSOLUTE + "/Models/"

NUMBER = 50000

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class ImageData(Dataset):
    def __init__(self, csvtruc, transform = None):
        self.transform = transform
        self.images = []
        self.resultats = []
        with open(csvtruc, 'r') as fichier:
            truc = csv.reader(fichier, delimiter = ',')
            for ligne in truc:
                if ligne != []:
                    image, resultat = ligne[0].split(',')
                    self.images.append(self.transform(cv2.imread(image)).float())
                    """self.images.append(image)"""
                    resultat = int(resultat)
                    if resultat == 0:
                        self.resultats.append(0)
                    else:
                        self.resultats.append(1)

    def __getitem__(self, index):
        """image = self.transform(cv2.imread(self.images[index])).float()"""
        image = self.images[index]
        resultat = self.resultats[index]
        return image, resultat

    def __len__(self):
        return len(self.resultats)
def load():
    global set_images
    global imagesLoader
    set_images = ImageData("D:/Documents/Prepa/TIPE/Imagesinfos.csv", transforms.Compose([transforms.ToTensor()]))
    imagesLoader = torch.utils.data.DataLoader(set_images, batch_size = 512, shuffle = True, pin_memory=True, num_workers=0)
    print('Images chargées.')

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.epochs = 0
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
        self.fc4 = nn.Linear(10, 2)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return x

net = Net()
net.to(device, non_blocking=True)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr = 0.001, momentum = 0.9)

def train(number):
    for epoch in range(number):
        running_loss = 0.0
        for i, data in enumerate(imagesLoader, 0):
            input, expected = data[0].to(device, non_blocking=True), data[1].to(device, non_blocking=True)
            optimizer.zero_grad()
            outputs = net(input)
            loss = criterion(outputs, expected)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print('Epoch : ' + str(epoch) + ' loss : ' + str(running_loss))
        net.epochs += 1

def test(altered, numero):
    if altered:
        image = set_images[NUMBER + numero][0].unsqueeze(0).to(device)
    else:
        image = set_images[numero][0].unsqueeze(0).to(device)
    return net(image)

def testSome(Number):
    totalChaque = Number
    global NUMBER
    Altered = 0
    for i in np.random.randint(0, NUMBER, size = (Number,)):
        res = test(True, i)
        if res[0][1] > res[0][0]:
            Altered += 1
    Normal = 0
    for i in np.random.randint(0, NUMBER, size = (Number,)):
        res = test(False, i)
        if res[0][1] < res[0][0]:
            Normal += 1
    print("Pour normal : " + str(Normal / totalChaque) + " et altéré : " + str(Altered / totalChaque))

def saveModel(nom):
    torch.save(net.state_dict(), pathModels + nom)

def loadModel(nom):
    net.load_state_dict(torch.load(pathModels + nom))
    net.eval()

def show():
    activation = {}
    def get_activation(name):
        def hook(model, input, output):
            activation[name] = output.detach()
        return hook

    net.conv2.register_forward_hook(get_activation('conv2'))
    data = set_images[0][0].to(device, non_blocking=True)
    output = net(data.unsqueeze(0))

    act = activation['conv2'].squeeze().cpu()
    fir, axarr = plt.subplots(act.size(0))
    for idx in range(act.size(0)):
        axarr[idx].imshow(act[idx])
    plt.show()
