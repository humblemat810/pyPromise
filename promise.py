
from thennable_thread import thennable_thread
from typing import Union, List
from threading import Thread
def await_start_next(last_th: "ThreadWithReturnValue", next_th: "ThreadWithReturnValue"):
    if last_th is not None:
        last_th.end_event.wait()
    if last_th.error_event.is_set():
        pass
    else:
        if last_th is not None:
            next_th._args = [last_th._return] + next_th._args
        else:
            #may behave insert none here
            # nothing indicate it has no result no parent
            pass
        if next_th._started.is_set():
            pass
        else:
            next_th.start()
class Promise ():
    auto_fire = True
    def resolve(self, value):
        self.resolve_value = value
    def reject(self, reason):
        self.reject_reason = reason
    def __init__(self, f_of_resolve_reject,  *args, **kwargs):
        self.resolve_value = None
        self.reject_reason = None
        #self.promise_resolved : Event = Event()
        if len(args) == 0:
            if issubclass(type(f_of_resolve_reject), thennable_thread):
                th = f_of_resolve_reject
            else:
                if callable(f_of_resolve_reject):
                    th = thennable_thread(target = f_of_resolve_reject, is_promise = True, args = (self.resolve, self.reject), kwargs = kwargs)
                    
                    
                else:
                    raise(ValueError("f_of_resolve_reject has to be thread or callable" ))
                    
            self.th = th
        else:
            self.th = thennable_thread( *args, is_promise = True, **kwargs)
            self.th.is_promise = True
        if self.auto_fire:
            self.fire()
        self.promise_resolved = self.th.end_event
    def fire(self):
        if self.th._started.is_set():
            pass
        else:
            
            if self.th.parent is not None:
                wsn_th = Thread(target= await_start_next, args = [self.th.parent, self.th])
                wsn_th.start()
            else:
                self.th.start()
    def then(self, *args, **kwargs):
        return Promise(self.th.then(*args, **kwargs))
        
    def done(self, *args, **kwargs):
        return Promise(self.th.done(*args, **kwargs))
            # internal thread reference
class Deferred(Promise):
    auto_fire = False

def when(ls_of_callable_or_promise: List[Union[callable, "thennable_thread" ]]):
    if type(ls_of_callable_or_promise) is list:
        if all(map( lambda x :  callable(type(x) or 
                                issubclass(type(x), thennable_thread)),
                                ls_of_callable_or_promise)) :
            def callback(resolve: callable, reject: callable):
                try:
                    promises = []
                    resolve_pred = None
                    for i in ls_of_callable_or_promise:
                        if not issubclass(type(i), thennable_thread):
                            i = Promise(i)
                            i.th.resolve_pred = resolve_pred
                            resolve_pred = i.th
                        promises.append(i)

                    [i.th.end_event.wait() for i in promises]
                    return resolve([i.th._return for i in promises])
                except Exception as e:
                    return reject(e)
            return Promise(f_of_resolve_reject = callback)
        else:
            return Promise(f_of_resolve_reject = lambda x,y : x(ls_of_callable_or_promise))

if __name__=="__main__":
    import time
    def e (*arg, **kwarg):
        print("e+ , prev arg = ", arg, '\n')
        raise(Exception('test for error'))
    def f (*arg):
        time.sleep(4)
        print("sleep+f, prev arg = ", arg, '\n')
        return 'ff' + str(arg)
    def g (*arg, **kwarg):
        print('g+, prev arg = ",',arg, 'prev kwarg =', kwarg, '\n')
        return str(arg) + "gg"
    def h (err):
        if err is None:
            print("h + err is none")
        else:
            raise (BaseException(str(err)))
    def prom_compatible(resolve: callable, reject: callable):
        import random
        a=random.random()
        if  a < 0.5:
            res = str(a) + ' less than 0.5'
            print(res)
            resolve("resolve" +str(a) + ' less than 0.5')
        else:
            res = "reject" +str(a) + ' more than equal 0.5'
            print(res)
            reject(str(a) + ' more than equal 0.5')
    def prom_test():
        prom = when([f])
        prom.th.promise_resolved_event.wait()
        print(prom.th.promise_resolved_event.is_set())
        print(type(prom))
        
        prom.done(g)
        dprom = Deferred(prom_compatible)
        dprom.fire()
    prom_test()
    n_d = 4
    dlist = [Deferred(prom_compatible) for i in range(n_d)]
    for i in range(n_d):
        #dprom = Deferred2(prom_compatible)
        #print(dprom.th._target)
        dlist[i].fire()
    for i in range(n_d):
        dlist[i].promise_resolved.wait()
        
        print(dlist[i].resolve_value, dlist[i].reject_reason)
    #prom_test()