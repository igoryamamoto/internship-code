# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 17:03 2017

@author: Igor Yamamoto
"""
import numpy as np
from cvxopt import matrix, solvers


class GPCController(object):
    def __init__(self, system, Ts, p, m, Q, R, du_min, du_max):
        self.system = system
        self.Ts = Ts
        self.nu = system.nu
        self.ny = system.ny
        self.p = p
        self.m = m
        self.Q = Q
        self.R = R
        self.du_min = du_min
        self.du_max = du_max
        self.G = self.initialize_G()
        AB = self.create_AB()
        self.A_til = AB[0]
        self.B = AB[1]

    def create_matrix_G(self, g, p, m):
        g = np.append(g[:p],np.zeros(m-1))
        G = np.array([])
        for i in range(p):
            G = np.append(G,[g[i-j] for j in range(m)])
        return np.resize(G,(p,m))

    def initialize_G(self):
        T = np.array(range(1, 200, self.Ts))
        g11, g12, g21, g22 = self.system.step_response(T=T)
        G11 = self.create_matrix_G(g11,self.p,self.m)
        G12 = self.create_matrix_G(g12,self.p,self.m)
        G21 = self.create_matrix_G(g21,self.p,self.m)
        G22 = self.create_matrix_G(g22,self.p,self.m)
        G1 = np.hstack((G11,G12))
        G2 = np.hstack((G21,G22))
        G = np.vstack((G1,G2))
        return G

    def create_AB(self):
        Bm11 = np.array([-0.19])
        Am11 = np.array([1, -1])
        Am11_til = np.convolve(Am11, [1,-1])

        Bm12 = np.array([-0.08498])
        Am12 = np.array([1, -0.95])
        Am12_til = np.convolve(Am12, [1,-1])

        Bm21 = np.array([-0.02362])
        Am21 = np.array([1, -0.969])
        Am21_til = np.convolve(Am21, [1,-1])

        Bm22 = np.array([0.235])
        Am22 = np.array([1, -1])
        Am22_til = np.convolve(Am22, [1,-1])
        return [[Am11_til, Am12_til, Am21_til, Am22_til],
                [Bm11, Bm12, Bm21, Bm22]]

    def calculate_control(self, w, **kwargs):
        dm = 0
        y11_f = np.zeros(self.p)
        y12_f = np.zeros(self.p)
        y21_f = np.zeros(self.p)
        y22_f = np.zeros(self.p)
        # Free Response
        du1, du2 = kwargs['current_du']
        du1_f, du2_f = kwargs['du_past']
        y11_aux, y12_aux, y21_aux, y22_aux = kwargs['y_past']
        for j in range(self.p):
            if j <= dm:
                du1_f = du1
                du2_f = du2
            else:
                du1_f = du2_f = np.array(0)
            y11_f[j] = -y11_aux.dot(self.A_til[0][1:]) + du1_f.dot(self.B[0])
            y12_f[j] = -y12_aux.dot(self.A_til[1][1:]) + du2_f.dot(self.B[1])
            y21_f[j] = -y21_aux.dot(self.A_til[2][1:]) + du1_f.dot(self.B[2])
            y22_f[j] = -y22_aux.dot(self.A_til[3][1:]) + du2_f.dot(self.B[3])
            y11_aux = np.append(y11_f[j], y11_aux[:-1])
            y12_aux = np.append(y12_f[j], y12_aux[:-1])
            y21_aux = np.append(y21_f[j], y21_aux[:-1])
            y22_aux = np.append(y22_f[j], y22_aux[:-1])
        f = np.append(y11_f+y12_f, y21_f+y22_f)
        # Solver Inputs
        H = matrix((2*(self.G.T.dot(self.Q).dot(self.G)+self.R)).tolist())
        q = matrix((2*self.G.T.dot(self.Q).dot(f-w)).tolist())
        A = matrix(np.hstack((np.eye(self.nu*self.m),-1*np.eye(self.nu*self.m))).tolist())
        b = matrix([self.du_max]*self.nu*self.m+[-self.du_min]*self.nu*self.m)
        # Solve
        sol = solvers.qp(P=H,q=q,G=A,h=b)
        dup = list(sol['x'])
        s = sol['status']
        j = sol['primal objective']
        return dup, j, s
