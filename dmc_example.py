# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 10:58:03 2017

@author: Ígor Yamamoto
"""
import numpy as np
import matplotlib.pyplot as plt
from cvxopt import matrix, solvers

def create_matrix_G(g, p, m):
    g = np.append(g,np.zeros(m-1))
    G = np.array([])
    for i in range(p):
        G = np.append(G,[g[i-j] for j in range(m)])  
    return np.resize(G,(p,m))
    
# prediction horizon
p = 15
# control horizon
m = 5
# number of inputs
nu = 2
# number of outputs
ny = 2

#%% vectors with step responses till t=15s w/ T = 1s
# gij -> output i relative to input j
# Modelo 1/s+1
g11 = np.array([
    0.6321,
    0.8647,
    0.9502,
    0.9817,
    0.9933,
    0.9975,
    0.9991,
    0.9997,
    0.9999,
    1.0000,
    1.0000,
    1.0000,
    1.0000,
    1.0000,
    1.0000
])
g12 = g21 = g22 = g11
#%% Create Dynamic Matrix
G11 = create_matrix_G(g11,p,m)
G12 = create_matrix_G(g12,p,m)
G21 = create_matrix_G(g21,p,m)
G22 = create_matrix_G(g22,p,m)   
G1 = np.hstack((G11,G12))
G2 = np.hstack((G21,G22))
G = np.vstack((G1,G2))
# Free respose
f = np.zeros(p*ny)
# References
w = np.array([2]*p+[2]*p)
# weights
Q = np.diag(np.ones(p*ny))
R = np.diag([10**-2]*m*nu)
#%% solver inputs
H = matrix((2*np.transpose(G).dot(Q).dot(G)+R).tolist())
q = matrix((2*np.transpose(G).dot(Q).dot(f-w)).tolist())
A = matrix(np.diag(np.ones(nu*m)).tolist()+np.diag(-1*np.ones(nu*m)).tolist())
b = matrix([0.2]*2*nu*m)
# solve
sol = solvers.qp(P=H,q=q,G=A.T,h=b)
sol_x = sol['x']
print(sol_x)
#%%
du1 = np.array([sol_x[i] for i in range(m)])
du2 = np.array([sol_x[i+m] for i in range(m)])
x11 = G11.dot(du1)
x12 = G12.dot(du2)
x21 = G21.dot(du1)
x22 = G22.dot(du2)
plt.plot(x11+x12)
plt.plot(x21+x22)
plt.legend(['x1','x2'])