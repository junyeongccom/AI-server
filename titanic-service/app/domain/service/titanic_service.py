import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split
from app.domain.model.data_schema import DataSchema
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
"""
PassengerId  고객ID,
Survived 생존여부,
Pclass 승선권 1 = 1등석, 2 = 2등석, 3 = 3등석,
Name,
Sex,
Age,
SibSp 동반한 형제, 자매, 배우자,
Parch 동반한 부모, 자식,
Ticket 티켓번호,
Fare 요금,
Cabin 객실번호,
Embarked 승선한 항구명 C = 쉐브루, Q = 퀸즈타운, S = 사우스햄튼

print(f'결정트리 활용한 검증 정확도 {None}')
print(f'랜덤포레스트 활용한 검증 정확도 {None}')
print(f'나이브베이즈 활용한 검증 정확도 {None}')
print(f'KNN 활용한 검증 정확도 {None}')
print(f'SVM 활용한 검증 정확도 {None}')
"""
class TitanicService:
    def __init__(self):
        self.data_schema = DataSchema()
        self.context = 'C:\\Users\\pakjk\\Documents\\2025\\kpmg2501\\demo2501\\v2\\ai-server\\titanic-service\\app\\stored_data\\'

    def load_data(self, fname: str) -> pd.DataFrame:
        return pd.read_csv(self.context + fname)
    
    def preprocess(self, train_fname: str, test_fname: str) -> dict:
        print("-------- 모델 전처리 시작 --------")
        # Load data
        train_df = self.load_data(train_fname)
        test_df = self.load_data(test_fname)
        
        # Store passenger IDs and labels
        passenger_ids = test_df['PassengerId']
        labels = train_df['Survived']
        
        # Drop target column from training data
        train_df = train_df.drop('Survived', axis=1)
        
        # Drop unnecessary features
        drop_features = ['SibSp', 'Parch', 'Cabin', 'Ticket']
        train_df = train_df.drop(drop_features, axis=1)
        test_df = test_df.drop(drop_features, axis=1)
        
        # Process titles
        train_df, test_df = self._process_titles(train_df, test_df)
        
        # Process gender
        train_df, test_df = self._process_gender(train_df, test_df)
        
        # Process embarked
        train_df, test_df = self._process_embarked(train_df, test_df)
        
        # Process age
        train_df, test_df = self._process_age(train_df, test_df)
        
        # Process fare
        train_df, test_df = self._process_fare(train_df, test_df)
        
        # Process pclass
        train_df, test_df = self._process_pclass(train_df, test_df)
        
        self._print_data_info(train_df, test_df)
        
        return {
            'train': train_df,
            'test': test_df,
            'passenger_ids': passenger_ids,
            'labels': labels
        }
    
    def _process_titles(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        # Extract titles
        train_df['Title'] = train_df['Name'].str.extract(r'([A-Za-z]+)\.', expand=False)
        test_df['Title'] = test_df['Name'].str.extract(r'([A-Za-z]+)\.', expand=False)
        
        # Map titles
        title_mapping = {'Mr': 1, 'Ms': 2, 'Mrs': 3, 'Master': 4, 'Royal': 5, 'Rare': 6}
        
        # Replace titles
        for df in [train_df, test_df]:
            df['Title'] = df['Title'].replace(['Countess', 'Lady', 'Sir'], 'Royal')
            df['Title'] = df['Title'].replace(['Capt','Col','Don','Dr','Major','Rev','Jonkheer','Dona','Mme'], 'Rare')
            df['Title'] = df['Title'].replace(['Mlle'], 'Mr')
            df['Title'] = df['Title'].replace(['Miss'], 'Ms')
            df['Title'] = df['Title'].fillna(0)
            df['Title'] = df['Title'].map(title_mapping)
        
        # Drop name column
        train_df = train_df.drop('Name', axis=1)
        test_df = test_df.drop('Name', axis=1)
        
        return train_df, test_df
    
    def _process_gender(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        gender_mapping = {'male': 0, 'female': 1}
        train_df['Gender'] = train_df['Sex'].map(gender_mapping)
        test_df['Gender'] = test_df['Sex'].map(gender_mapping)
        
        train_df = train_df.drop('Sex', axis=1)
        test_df = test_df.drop('Sex', axis=1)
        
        return train_df, test_df
    
    def _process_embarked(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        embarked_mapping = {'S': 1, 'C': 2, 'Q': 3}
        
        for df in [train_df, test_df]:
            df['Embarked'] = df['Embarked'].fillna('S')
            df['Embarked'] = df['Embarked'].map(embarked_mapping)
        
        return train_df, test_df
    
    def _process_age(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        # Fill missing ages
        for df in [train_df, test_df]:
            df['Age'] = df['Age'].fillna(-0.5)
        
        # Create age groups
        bins = [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
        labels = ['Unknown','Baby','Child','Teenager','Student','Young Adult','Adult', 'Senior']
        age_mapping = {'Unknown':0, 'Baby':1, 'Child':2, 'Teenager':3, 'Student':4,
                      'Young Adult':5, 'Adult':6, 'Senior':7}
        
        for df in [train_df, test_df]:
            df['AgeGroup'] = pd.cut(df['Age'], bins, labels=labels).map(age_mapping)
        
        train_df = train_df.drop('Age', axis=1)
        test_df = test_df.drop('Age', axis=1)
        
        return train_df, test_df
    
    def _process_fare(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        # TODO: Implement fare processing if needed
        return train_df, test_df
    
    def _process_pclass(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        # TODO: Implement pclass processing if needed
        return train_df, test_df
    

    # 머신러닝 : learning
    @staticmethod
    def create_k_fold():
        return KFold(n_splits=10, shuffle= True, random_state=0 )

    def accuracy_by_dtree(self, this):
        score = cross_val_score(DecisionTreeClassifier(),
                                this.train,
                                this.label,
                                cv=KFold(n_splits=10, shuffle=True, random_state=0),
                                n_jobs=1,
                                scoring= 'accuracy')
        return round(np.mean(score) * 100, 2)


    def accuracy_by_random_forest(self, this):
        score = cross_val_score(RandomForestClassifier(),
                                this.train,
                                this.label,
                                cv=KFold(n_splits=10, shuffle=True, random_state=0),
                                n_jobs=1,
                                scoring='accuracy')
        return round(np.mean(score) * 100, 2)


    def accuracy_by_naive_bayes(self, this):
        score = cross_val_score(GaussianNB(),
                                this.train,
                                this.label,
                                cv=KFold(n_splits=10, shuffle=True, random_state=0),
                                n_jobs=1,
                                scoring='accuracy')
        return round(np.mean(score) * 100, 2)

    def accuracy_by_knn(self, this):
        score = cross_val_score(KNeighborsClassifier(),
                                this.train,
                                this.label,
                                cv=KFold(n_splits=10, shuffle=True, random_state=0),
                                n_jobs=1,
                                scoring='accuracy')
        return round(np.mean(score) * 100, 2)

    def accuracy_by_svm(self, this):
        return round(np.mean(cross_val_score(SVC(),
                                this.train,
                                this.label,
                                cv=KFold(n_splits=10, shuffle=True, random_state=0),
                                n_jobs=1,
                                scoring='accuracy')) * 100, 2)
    
    
    def _print_data_info(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
        print('*' * 100)
        print(f'1. Train type: {type(train_df)}')
        print(f'2. Train columns: {train_df.columns}')
        print(f'3. Train head:\n{train_df.head()}')
        print(f'4. Train null counts:\n{train_df.isnull().sum()}')
        print(f'5. Test type: {type(test_df)}')
        print(f'6. Test columns: {test_df.columns}')
        print(f'7. Test head:\n{test_df.head()}')
        print(f'8. Test null counts:\n{test_df.isnull().sum()}')
        print('*' * 100)



