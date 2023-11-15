
from thennable_thread import thennable_thread, await_start_next
from typing import Union, List
from threading import Thread

class Deferred(thennable_thread):
    def __init__(self, *args, target = None, **kwargs):
        self.th=self
        self.auto_fire = False
        if target is None:
            target = args[0]
            args = args[1:]
        super().__init__( *args, target=target,**kwargs)
        if self.th._started.is_set():
            pass
        else:
            if self.auto_fire:
                if self.th.parent is not None:
                    wsn_th = Thread(target= await_start_next, args = [self.th.parent, self.th])
                    wsn_th.start()
                else:
                    self.th.start()

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
                    th = thennable_thread(target = f_of_resolve_reject, args = (self.resolve, self.reject), kwargs = kwargs)
                    
                    
                else:
                    raise(ValueError("f_of_resolve_reject has to be thread or callable" ))
                    
            self.th = th
        else:
            self.th = thennable_thread( *args, **kwargs)
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
    def done(self, *args, **kwargs):
        return Promise(self.th.done(*args, **kwargs))
            # internal thread reference
class Deferred2(Promise):
    auto_fire = False
from threading import Event
def when(ls_of_callable_or_promise: List[Union[callable, "thennable_thread" ]]):
    
    def callback(resolve: callable, reject: callable):
        try:
            promises = []
            for i in ls_of_callable_or_promise:
                if not issubclass(type(i), thennable_thread):
                    i = Promise(i)
                promises.append(i)

            [i.th.end_event.wait() for i in promises]
            return resolve([i.th._return for i in promises])
        except Exception as e:
            return reject(e)
    return Promise(f_of_resolve_reject = callback)

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
            resolve(str(a) + ' less than 0.5')
        else:
            reject(str(a) + ' more than equal 0.5')
    def prom_test():
        prom = when([f])
        prom.th.end_event.wait()
        print(prom.th.end_event.is_set())
        print(type(prom))
        
        prom.done(g)
        dprom = Deferred2(prom_compatible)
        dprom.fire()
    n_d = 4
    dlist = [Deferred2(prom_compatible) for i in range(n_d)]
    for i in range(n_d):
        #dprom = Deferred2(prom_compatible)
        #print(dprom.th._target)
        dlist[i].fire()
        
        dlist[i].promise_resolved.wait()
        
        print(dlist[i].resolve_value, dlist[i].reject_reason)
    #prom_test()