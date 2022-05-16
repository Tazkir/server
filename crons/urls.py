from django.conf.urls import url
from . import views

app_name = 'crons'

urlpatterns = [
    url(r'^purge_old_messages$', views.PurgeOldMessages.as_view()),
    url(r'^projects_needs_upgrade$', views.ProjectsNeedsUpgrade.as_view()),
    url(r'^apply_chat_updates$', views.ApplyChatUpdates.as_view()),
    url(r'^sync_member_ids$', views.SyncMemberIDs.as_view()),
    url(r'^prune_biz_chat$', views.PruneBusinessChat.as_view()),
    url(r'^receive_buffer$', views.ReceiveBuffer.as_view()),
    url(r'^owner_to_admin$', views.OwnerToAdmin.as_view()),
    url(r'^business_accounts$', views.BusinessAccounts.as_view()),
]
