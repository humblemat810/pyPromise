
from thennable_thread import thennable_thread, await_start_next
from typing import Union, List
from threading import Thread

class Deferred(thennable_thread):
    def __init__(self, *args, target = None, **kwargs):
        self.th=self
        if target is None:
            target = args[0]
            args = args[1:]
        super().__init__( *args, target=target,**kwargs)
        
class Promise ():
    def __init__(self, f_of_resolve_reject,  *args, **kwargs):
        if len(args) > 0:
            if issubclass(type(f_of_resolve_reject), thennable_thread):
                th = f_of_resolve_reject
            else:
                if callable(f_of_resolve_reject):
                    th = thennable_thread(target = f_of_resolve_reject, args = args, kwargs = kwargs)
                else:
                    raise(ValueError("f_of_resolve_reject has to be thread or callable" ))
                    
            self.th = th
        else:
            self.th = thennable_thread( *args, **kwargs)
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
def when(ls_of_callable_or_promise: List[Union[callable, "thennable_thread" ]]):
        
    def callback():
        promises = []
        for i in ls_of_callable_or_promise:
            if not issubclass(type(i), thennable_thread):
                i = Promise(i)
            promises.append(i)

        [i.th.end_event.wait() for i in promises]
        return [i.th._return for i in promises]
    return Promise(target = callback)