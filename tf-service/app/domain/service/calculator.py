import tensorflow as tf


class Calculator:
    def __init__(self):
        pass
        
    @tf.function
    def plus(self, num1, num2): return tf.add(num1, num2)
    
    @tf.function
    def minus(self, num1, num2): return tf.subtract(num1, num2)
    
    @tf.function
    def multiple(self, num1, num2): return tf.multiply(num1, num2)
    
    @tf.function
    def div(self, num1, num2): return tf.divide(num1, num2)


    def sample(self):
        mnist = tf.keras.datasets.mnist
        print(f"❗😃🎃mnist: {mnist}")

        (x_train, y_train),(x_test, y_test) = mnist.load_data()
        print(f"❗😃🎃x_train: {x_train}")
        print(f"❗😃🎃y_train: {y_train}") 
        print(f"❗😃🎃x_test: {x_test}")
        print(f"❗😃🎃y_test: {y_test}")
        x_train, x_test = x_train / 255.0, x_test / 255.0
        print(f"❗😃🎃x_train.shape: {x_train.shape}")
        print(f"❗😃🎃x_test.shape: {x_test.shape}")

        model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(10, activation='softmax')
        ])
        print(f"❗😃🎃model: {model}")

        model.compile(optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'])
        print(f"❗😃🎃model: {model}")

        model.fit(x_train, y_train, epochs=5)
        print(f"❗😃🎃model: {model}")
        model.evaluate(x_test, y_test)
        print(f"❗😃🎃model: {model}")