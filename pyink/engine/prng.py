class PRNG:
    def __init__(self, seed: int):
        self.seed = seed % 2147483647
        if self.seed <= 0:
            self.seed += 2147483646

    def next(self) -> int:
        self.seed = (self.seed * 48271) % 2147483647
        return self.seed

    def nextFloat(self) -> float:
        return (self.next() - 1) / 2147483646
