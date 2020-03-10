# chaoxingautosign</br>
 ## 超星尔雅自动签到</br>
 使用手机扫描二维码登录</br>

### ＃需求</br>
opencv</br>
numpy</br>
pyzbar</br>

打开 [autosign.py](/autosign.py)</br>
可以看到两个类：</br>
### AutoSign类 对登录，获取信息，以及扫描签到进行了封装</br>
AutoSign类在初始化时会进行登陆操作，初始化可选参数sign_frequency_minutes（多久扫描一次，指分钟）</br>
包括获取登陆二维码并通过opencv打印出来，获取登陆状态，以及登陆后的uid和cookies</br>

AutoSign类中对外直接暴露的两个函数</br>
run（注意，这个函数很好用，但他是一个死循环）</br>
run_one（他仅仅扫描一次）</br>
他们不需要任何参数</br>
其余函数并不建议直接使用，例如_AutoSign__get_class_json(在类中为__get_class_json)</br>
### CheckSignThread（基于threading.Thread）其中组合了AutoSign类</br>
CheckSignThread类的父类是threading.Thread</br>
他仅仅封装了停止,恢复停止,以及结束等函数</br>
例子放在了main里面，但你直接运行时不会触发（因为在他前面的是AutoSign类中run函数，他是个死循环）</br>
CheckSignThread类和AutoSign类中的run_one都是提供给那些希望自己控制次数和时间的人</br>
（当然，你也可以快捷的在构造AutoSign时提供扫描的间隔时间，并在run中使用他们）</br>

这个小小的脚本也许不会有人发现？😀</br>


