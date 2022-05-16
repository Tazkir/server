from server.settings import get_secret

from mixpanel import Mixpanel


class MixPanel:
    def __init__(self):
        self.mp = Mixpanel(get_secret('MIXPANEL'))

    def track(self, user_id=None, event=None, data=None):
        if get_secret('PIPELINE') == 'production':
            try:
                self.mp.track(user_id, event, data)

            except Exception as e:
                print(str(e))


mix_panel = MixPanel()
