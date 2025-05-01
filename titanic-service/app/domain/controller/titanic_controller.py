from sklearn.svm import SVC
import pandas as pd
from app.domain.service.titanic_service import TitanicService
'''
print(f'결정트리 활용한 검증 정확도 {None}')
print(f'랜덤포레스트 활용한 검증 정확도 {None}')
print(f'나이브베이즈 활용한 검증 정확도 {None}')
print(f'KNN 활용한 검증 정확도 {None}')
print(f'SVM 활용한 검증 정확도 {None}')
'''
class TitanicController:

    service = TitanicService()

    def preprocess(self, train_fname, test_fname):
        """
        Preprocess the Titanic dataset using TitanicService
        Args:
            train_fname: Training data file name
            test_fname: Test data file name
        Returns:
            Processed data object
        """
        return self.service.preprocess(train_fname, test_fname)
    
    def learning(self, train, test):
        service = self.service
        this = self.preprocess(train, test)
        this.label = service.create_label(this)
        this.train = service.crate_train(this)
        print(f'결정트리 활용한 검증 정확도 {service.accuracy_by_dtree(this)}')
        print(f'랜덤포레스트 활용한 검증 정확도 {service.accuracy_by_rforest(this)}')
        print(f'나이브베이즈 활용한 검증 정확도 {service.accuracy_by_nb(this)}')
        print(f'KNN 활용한 검증 정확도 {service.accuracy_by_knn(this)}')
        print(f'SVM 활용한 검증 정확도 {service.accuracy_by_svm(this)}')
        

    def submit(self, train, test):
        service = self.service
        this = self.preprocess(train, test)
        this.label = service.create_label(this)
        this.train = service.crate_train(this)
        clf = SVC()
        clf.fit(this.train, this.label)
        prediction = clf.predict(this.test)
        pd.DataFrame(
            {'PassengerId' : this.id, 'Survived': prediction}
        ).to_csv('./datas/submission.csv', index_label=False)
    
 
    
 