def forward_(updates, mu, nu, lr, b1, b2, eps, eps_root, count): ...


def forwardMu(updates, mu, b1): ...


def forwardNu(updates, nu, b2): ...


def forwardUpdates(new_mu, new_nu, lr, b1, b2, eps, eps_root, count): ...


def backwardMu(dmu, updates, mu, b1): ...


def backwardNu(dnu, updates, nu, b2): ...


def backwardUpdates(dupdates, updates, new_mu, new_nu, lr, b1, b2, count): ...