
class CallbackEnabledClass():
    '''
    Superclass for any classes wanting to add a callback listener
    '''
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self._callbacks=list()
        self._callback_paused=False

    def add_update_callback(self,cb):
        self._callbacks.append(cb)

    def remove_update_callback(self,cb):
        self._callbacks.remove(cb)

    def _call_update_callbacks(self,data=None):
        if self._callback_paused:
            return
        for i in self._callbacks:
            i(data)

    def _pause_callbacks(self):
        self._callback_paused=True
    def _unpause_callbacks(self):
        self._callback_paused=False

