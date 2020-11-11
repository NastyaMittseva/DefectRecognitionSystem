# DefectRecognitionSystem
Система автоматического распознавания дефектов сварных швов по ренгеновским снимкам.
### Инструкция по работе с системой
Разработанный веб-интерфейс предоставляет 2 версии приложения - демонстрационную (ограниченную) и полную. Демонстрационная версия размещена по адресу http://37.75.252.29:1236/, логин: test, пароль:87654321.

Для входа в систему необходимо пройти авторизацию, и затем вы попадете на главную страницу приложения.
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/main.png)
Затем необходимо нажать кнопку для загрузки тестового изображения, и из тестовой базы отобразиться снимок.
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/load_image.png)
После можно выбрать одно из трех видов распознавания - распознавание области шва, распознавание дефектов или классификация дефектов. Результаты распознавания записываются в таблицу.
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/results.png)
В таблице с результатами можно выбрать одну или несколько строк и нажать на кнопку "Show results". Результаты распозавания отобразятся в графическом виде с описанием ниже. 
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/weld_recognition.png)
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/defect_recognition.png)
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/defect_classification.png)
Также можно просматривать всю историю распознавания изображений, которые были загружены текущим пользователем. Для этого необходимо в правом верхнем углу сменить страницу на "Events history".
![](https://github.com/NastyaMittseva/DefectRecognitionSystem/blob/master/screens/history.png)
В полной версии функционал не отличается, едиственное отличие - пользователю предоставляется возможность загружать снимки в форматах .jpg, .png, а также и в рентгеновском формате .VRC.