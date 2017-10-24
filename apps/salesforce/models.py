from django.contrib.postgres.fields import JSONField, HStoreField
from django.db import models
from core.mixins import TimeStampedMixin
from visualizer.models import User, Client
from psqlextra.manager import PostgresManager
from psqlextra.query import ConflictAction

from stringcase import pascalcase


class SalesforceCustomFieldMapping(TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_custom_field_mapping'

    client = models.ForeignKey(Client)
    entity = models.CharField(max_length=50, db_index=True, blank=False, null=False)

    # Sample Data: "field1_mapped_to"=>"ARR", "field1_sfdc_name"=>"ARR__c"
    # Update Query: update salesforce_custom_field_mapping set
    #               "mapping" = 'field1_sfdc_name=>ARR__c,field1_mapped_to=>ARR'::hstore
    #               where id = 1;
    mapping = HStoreField()


class SalesforceEntityDescription(TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_entity_description'

    client = models.ForeignKey(Client, db_index=True)
    entity_name = models.TextField(db_index=True)
    standard_fields = JSONField()
    custom_fields = JSONField()


class SalesforceEntityMixin(models.Model):
    class Meta:
        abstract = True
        unique_together = ('client', 'sfdc_id')

    commit_list = []
    objects = PostgresManager()

    client = models.ForeignKey(Client)

    sfdc_id = models.TextField(db_index=True)
    rest_of_data = JSONField(default={})

    @classmethod
    def field_names(cls):
        return [f.name for f in cls._meta.fields]

    @classmethod
    def commit_or_delete_from_bulk_row(cls, row, client: Client):
        """
        This function deletes the entry if necessary. Otherwise it commits the upsert request
        :param row:
        :param client:
        :return:
        """

        if row.get('IsDeleted', 'false').lower() == 'true':
            print("one deletion")
            cls.objects.filter(client=client, sfdc_id=row['Id']).delete()
            return

        field_names = cls.field_names()
        overrides = cls.field_mapping_overrides()

        entity_dict = {}

        for field_name in field_names:
            row_index = pascalcase(field_name)
            try:
                row[row_index]
            except KeyError:
                continue
            dict_index = overrides[field_name] if (field_name in overrides) else field_name
            entity_dict[dict_index] = row[row_index]
            del row[row_index]

        entity_dict['rest_of_data'] = row
        entity_dict['client'] = client

        cls.commit_list.append(entity_dict)

    @classmethod
    def push_save_commits(cls):
        if len(cls.commit_list) < 1:
            print("Nothing to save")
            return

        print("Saving {} items".format(len(cls.commit_list)))

        cls.objects\
            .on_conflict(['client', 'sfdc_id'], ConflictAction.UPDATE)\
            .bulk_insert(cls.commit_list)

        cls.commit_list.clear()

    @classmethod
    def field_mapping_overrides(cls):
        """
        Override this method if needed for the subclasses to
        do field mapping overriding.

        It is a dictionary of
            * key: expected field name in the model
            * value: real field name in the model
        Example: key: "id", value: "sfdc_id" => { "id": "sfdc_id" }
        :return: dict
        """
        return {
            'id': 'sfdc_id',
        }


class SalesforceField(models.TextField):
    def __init__(self, *args, **kwargs):
        kwargs['default'] = ''
        super(SalesforceField, self).__init__(*args, **kwargs)


class SalesforceAccount(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_account'

    master_record_id = SalesforceField()
    name = SalesforceField()
    type = SalesforceField()
    parent_id = SalesforceField()
    billing_street = SalesforceField()
    billing_city = SalesforceField()
    billing_state = SalesforceField()
    billing_postal_code = SalesforceField()
    billing_country = SalesforceField()
    billing_state_code = SalesforceField()
    billing_country_code = SalesforceField()
    billing_latitude = SalesforceField()
    billing_longitude = SalesforceField()
    billing_geocode_accuracy = SalesforceField()
    shipping_street = SalesforceField()
    shipping_city = SalesforceField()
    shipping_state = SalesforceField()
    shipping_postal_code = SalesforceField()
    shipping_country = SalesforceField()
    shipping_state_code = SalesforceField()
    shipping_country_code = SalesforceField()
    shipping_latitude = SalesforceField()
    shipping_longitude = SalesforceField()
    shipping_geocode_accuracy = SalesforceField()
    phone = SalesforceField()
    website = SalesforceField()
    photo_url = SalesforceField()
    industry = SalesforceField()
    annual_revenue = SalesforceField()
    number_of_employees = SalesforceField()
    description = SalesforceField()
    owner_id = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    last_activity_date = SalesforceField()
    last_viewed_date = SalesforceField()
    last_referenced_date = SalesforceField()
    jigsaw_company_id = SalesforceField()
    account_source = SalesforceField()


class SalesforceAccountHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_account_history'

    account_id = SalesforceField(db_index=True)
    created_by_id = SalesforceField()
    created_date = SalesforceField()
    field = SalesforceField()
    old_value = SalesforceField()
    new_value = SalesforceField()


class SalesforceContact(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_contact'

    master_record_id = SalesforceField()
    account_id = SalesforceField(db_index=True)
    name = SalesforceField()
    first_name = SalesforceField()
    last_name = SalesforceField()
    salutation = SalesforceField()
    mailing_street = SalesforceField()
    mailing_city = SalesforceField()
    mailing_state = SalesforceField()
    mailing_postal_code = SalesforceField()
    mailing_country = SalesforceField()
    mailing_state_code = SalesforceField()
    mailing_country_code = SalesforceField()
    mailing_latitude = SalesforceField()
    mailing_longitude = SalesforceField()
    mailing_geocode_accuracy = SalesforceField()
    phone = SalesforceField()
    fax = SalesforceField()
    mobile_phone = SalesforceField()
    email = SalesforceField()
    title = SalesforceField()
    department = SalesforceField()
    lead_source = SalesforceField()
    description = SalesforceField()
    owner_id = SalesforceField(db_index=True)
    has_opted_out_of_email = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    last_activity_date = SalesforceField()
    last_c_u_request_date = SalesforceField()
    last_c_u_update_date = SalesforceField()
    last_viewed_date = SalesforceField()
    last_referenced_date = SalesforceField()
    email_bounced_reason = SalesforceField()
    email_bounced_date = SalesforceField()
    is_email_bounced = SalesforceField()
    photo_url = SalesforceField()
    jigsaw_contact_id = SalesforceField()


class SalesforceContactHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_contact_history'

    contact_id = SalesforceField(db_index=True)
    created_by_id = SalesforceField(db_index=True)
    created_date = SalesforceField()
    field = SalesforceField()
    old_value = SalesforceField()
    new_value = SalesforceField()


class SalesforceOpportunity(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_opportunity'

    account_id = SalesforceField(db_index=True)
    record_type_id = SalesforceField()
    name = SalesforceField()
    description = SalesforceField()
    stage_name = SalesforceField()
    amount = SalesforceField()
    probability = SalesforceField()
    close_date = SalesforceField()
    type = SalesforceField()
    next_step = SalesforceField()
    lead_source = SalesforceField()
    is_closed = SalesforceField()
    is_won = SalesforceField()
    forecast_category = SalesforceField()
    forecast_category_name = SalesforceField()
    campaign_id = SalesforceField()
    has_opportunity_line_item = SalesforceField()
    is_split = SalesforceField()
    pricebook2_id = SalesforceField()
    owner_id = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    last_activity_date = SalesforceField()
    fiscal_quarter = SalesforceField()
    fiscal_year = SalesforceField()
    fiscal = SalesforceField()
    last_viewed_date = SalesforceField()
    last_referenced_date = SalesforceField()
    synced_quote_id = SalesforceField()
    has_open_activity = SalesforceField()
    has_overdue_task = SalesforceField()


class SalesforceOpportunityHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_opportunity_history'

    opportunity_id = SalesforceField(db_index=True)
    created_by_id = SalesforceField()
    created_date = SalesforceField()
    stage_name = SalesforceField()
    amount = SalesforceField()
    expected_revenue = SalesforceField()
    close_date = SalesforceField()
    probability = SalesforceField()
    forecast_category = SalesforceField()
    system_modstamp = SalesforceField()


class SalesforceOpportunityFieldHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_opportunity_field_history'

    opportunity_id = SalesforceField(db_index=True)
    created_by_id = SalesforceField()
    created_date = SalesforceField()
    field = SalesforceField()
    old_value = SalesforceField()
    new_value = SalesforceField()


class SalesforceLead(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_lead'

    master_record_id = SalesforceField()
    last_name = SalesforceField()
    first_name = SalesforceField()
    salutation = SalesforceField()
    name = SalesforceField()
    title = SalesforceField()
    company = SalesforceField()
    street = SalesforceField()
    city = SalesforceField()
    state = SalesforceField()
    postal_code = SalesforceField()
    country = SalesforceField()
    state_code = SalesforceField()
    country_code = SalesforceField()
    latitude = SalesforceField()
    longitude = SalesforceField()
    geocode_accuracy = SalesforceField()
    address = SalesforceField()
    phone = SalesforceField()
    mobile_phone = SalesforceField()
    fax = SalesforceField()
    email = SalesforceField()
    website = SalesforceField()
    photo_url = SalesforceField()
    description = SalesforceField()
    lead_source = SalesforceField()
    status = SalesforceField()
    industry = SalesforceField()
    annual_revenue = SalesforceField()
    number_of_employees = SalesforceField()
    owner_id = SalesforceField(db_index=True)
    has_opted_out_of_email = SalesforceField()
    is_converted = SalesforceField()
    converted_date = SalesforceField()
    converted_account_id = SalesforceField()
    converted_contact_id = SalesforceField()
    converted_opportunity_id = SalesforceField()
    is_unread_by_owner = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    last_activity_date = SalesforceField()
    last_viewed_date = SalesforceField()
    last_referenced_date = SalesforceField()
    jigsaw_contact_id = SalesforceField()
    email_bounced_reason = SalesforceField()
    email_bounced_date = SalesforceField()


class SalesforceTask(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_task'

    who_id = SalesforceField(db_index=True)
    what_id = SalesforceField(db_index=True)
    who_count = SalesforceField()
    what_count = SalesforceField()
    subject = SalesforceField()
    activity_date = SalesforceField()
    status = SalesforceField()
    priority = SalesforceField()
    is_high_priority = SalesforceField()
    owner_id = SalesforceField(db_index=True)
    description = SalesforceField()
    type = SalesforceField()
    account_id = SalesforceField(db_index=True)
    is_closed = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    is_archived = SalesforceField()
    call_duration_in_seconds = SalesforceField()
    call_type = SalesforceField()
    call_disposition = SalesforceField()
    call_object = SalesforceField()
    reminder_date_time = SalesforceField()
    is_reminder_set = SalesforceField()
    recurrence_activity_id = SalesforceField()
    is_recurrence = SalesforceField()
    recurrence_start_date_only = SalesforceField()
    recurrence_end_date_only = SalesforceField()
    recurrence_time_zone_sid_key = SalesforceField()
    recurrence_type = SalesforceField()
    recurrence_interval = SalesforceField()
    recurrence_day_of_week_mask = SalesforceField()
    recurrence_day_of_month = SalesforceField()
    recurrence_instance = SalesforceField()
    recurrence_month_of_year = SalesforceField()
    recurrence_regenerated_type = SalesforceField()
    task_subtype = SalesforceField()


class SalesforceUser(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_user'

    username = SalesforceField()
    last_name = SalesforceField()
    first_name = SalesforceField()
    name = SalesforceField()
    company_name = SalesforceField()
    division = SalesforceField()
    department = SalesforceField()
    title = SalesforceField()
    street = SalesforceField()
    city = SalesforceField()
    state = SalesforceField()
    postal_code = SalesforceField()
    country = SalesforceField()
    state_code = SalesforceField()
    country_code = SalesforceField()
    latitude = SalesforceField()
    longitude = SalesforceField()
    geocode_accuracy = SalesforceField()
    address = SalesforceField()
    email = SalesforceField()
    email_preferences_auto_bcc = SalesforceField()
    email_preferences_auto_bcc_stay_in_touch = SalesforceField()
    email_preferences_stay_in_touch_reminder = SalesforceField()
    sender_email = SalesforceField()
    sender_name = SalesforceField()
    signature = SalesforceField()
    stay_in_touch_subject = SalesforceField()
    stay_in_touch_signature = SalesforceField()
    stay_in_touch_note = SalesforceField()
    phone = SalesforceField()
    fax = SalesforceField()
    mobile_phone = SalesforceField()
    alias = SalesforceField()
    community_nickname = SalesforceField()
    badge_text = SalesforceField()
    is_active = SalesforceField()
    time_zone_sid_key = SalesforceField()
    user_role_id = SalesforceField()
    locale_sid_key = SalesforceField()
    receives_info_emails = SalesforceField()
    receives_admin_info_emails = SalesforceField()
    email_encoding_key = SalesforceField()
    profile_id = SalesforceField()
    user_type = SalesforceField()
    language_locale_key = SalesforceField()
    employee_number = SalesforceField()
    delegated_approver_id = SalesforceField()
    manager_id = SalesforceField()
    last_login_date = SalesforceField()
    last_password_change_date = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    offline_trial_expiration_date = SalesforceField()
    offline_pda_trial_expiration_date = SalesforceField()
    user_permissions_marketing_user = SalesforceField()
    user_permissions_offline_user = SalesforceField()
    user_permissions_avantgo_user = SalesforceField()
    user_permissions_call_center_auto_login = SalesforceField()
    user_permissions_mobile_user = SalesforceField()
    user_permissions_s_f_content_user = SalesforceField()
    user_permissions_interaction_user = SalesforceField()
    user_permissions_support_user = SalesforceField()
    user_permissions_chatter_answers_user = SalesforceField()
    forecast_enabled = SalesforceField()
    user_preferences_activity_reminders_popup = SalesforceField()
    user_preferences_event_reminders_checkbox_default = SalesforceField()
    user_preferences_task_reminders_checkbox_default = SalesforceField()
    user_preferences_reminder_sound_off = SalesforceField()
    user_preferences_disable_all_feeds_email = SalesforceField()
    user_preferences_disable_followers_email = SalesforceField()
    user_preferences_disable_profile_post_email = SalesforceField()
    user_preferences_disable_change_comment_email = SalesforceField()
    user_preferences_disable_later_comment_email = SalesforceField()
    user_preferences_dis_prof_post_comment_email = SalesforceField()
    user_preferences_apex_pages_developer_mode = SalesforceField()
    user_preferences_hide_c_s_n_get_chatter_mobile_task = SalesforceField()
    user_preferences_disable_mentions_post_email = SalesforceField()
    user_preferences_dis_mentions_comment_email = SalesforceField()
    user_preferences_hide_c_s_n_desktop_task = SalesforceField()
    user_preferences_hide_chatter_onboarding_splash = SalesforceField()
    user_preferences_hide_second_chatter_onboarding_splash = SalesforceField()
    user_preferences_dis_comment_after_like_email = SalesforceField()
    user_preferences_disable_like_email = SalesforceField()
    user_preferences_sort_feed_by_comment = SalesforceField()
    user_preferences_disable_message_email = SalesforceField()
    user_preferences_disable_bookmark_email = SalesforceField()
    user_preferences_disable_share_post_email = SalesforceField()
    user_preferences_enable_auto_sub_for_feeds = SalesforceField()
    user_preferences_disable_file_share_notifications_for_api = SalesforceField()
    user_preferences_show_title_to_external_users = SalesforceField()
    user_preferences_show_manager_to_external_users = SalesforceField()
    user_preferences_show_email_to_external_users = SalesforceField()
    user_preferences_show_work_phone_to_external_users = SalesforceField()
    user_preferences_show_mobile_phone_to_external_users = SalesforceField()
    user_preferences_show_fax_to_external_users = SalesforceField()
    user_preferences_show_street_address_to_external_users = SalesforceField()
    user_preferences_show_city_to_external_users = SalesforceField()
    user_preferences_show_state_to_external_users = SalesforceField()
    user_preferences_show_postal_code_to_external_users = SalesforceField()
    user_preferences_show_country_to_external_users = SalesforceField()
    user_preferences_show_profile_pic_to_guest_users = SalesforceField()
    user_preferences_show_title_to_guest_users = SalesforceField()
    user_preferences_show_city_to_guest_users = SalesforceField()
    user_preferences_show_state_to_guest_users = SalesforceField()
    user_preferences_show_postal_code_to_guest_users = SalesforceField()
    user_preferences_show_country_to_guest_users = SalesforceField()
    user_preferences_hide_s1_browser_u_i = SalesforceField()
    user_preferences_disable_endorsement_email = SalesforceField()
    user_preferences_path_assistant_collapsed = SalesforceField()
    user_preferences_cache_diagnostics = SalesforceField()
    user_preferences_show_email_to_guest_users = SalesforceField()
    user_preferences_show_manager_to_guest_users = SalesforceField()
    user_preferences_show_work_phone_to_guest_users = SalesforceField()
    user_preferences_show_mobile_phone_to_guest_users = SalesforceField()
    user_preferences_show_fax_to_guest_users = SalesforceField()
    user_preferences_show_street_address_to_guest_users = SalesforceField()
    user_preferences_lightning_experience_preferred = SalesforceField()
    user_preferences_preview_lightning = SalesforceField()
    user_preferences_hide_end_user_onboarding_assistant_modal = SalesforceField()
    user_preferences_hide_lightning_migration_modal = SalesforceField()
    user_preferences_hide_sfx_welcome_mat = SalesforceField()
    user_preferences_hide_bigger_photo_callout = SalesforceField()
    user_preferences_global_nav_bar_w_t_shown = SalesforceField()
    user_preferences_global_nav_grid_menu_w_t_shown = SalesforceField()
    user_preferences_create_l_e_x_apps_w_t_shown = SalesforceField()
    user_preferences_favorites_w_t_shown = SalesforceField()
    user_preferences_record_home_section_collapse_w_t_shown = SalesforceField()
    user_preferences_record_home_reserved_w_t_shown = SalesforceField()
    user_preferences_favorites_show_top_favorites = SalesforceField()
    contact_id = SalesforceField(db_index=True)
    account_id = SalesforceField(db_index=True)
    call_center_id = SalesforceField()
    extension = SalesforceField()
    federation_identifier = SalesforceField()
    about_me = SalesforceField()
    full_photo_url = SalesforceField()
    small_photo_url = SalesforceField()
    is_ext_indicator_visible = SalesforceField()
    medium_photo_url = SalesforceField()
    digest_frequency = SalesforceField()
    default_group_notification_frequency = SalesforceField()
    last_viewed_date = SalesforceField()
    last_referenced_date = SalesforceField()
    banner_photo_url = SalesforceField()
    small_banner_photo_url = SalesforceField()
    medium_banner_photo_url = SalesforceField()
    is_profile_photo_active = SalesforceField()


class SalesforceUserRole(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_user_role'

    name = SalesforceField()
    parent_role_id = SalesforceField()
    rollup_description = SalesforceField()
    opportunity_access_for_account_owner = SalesforceField()
    case_access_for_account_owner = SalesforceField()
    contact_access_for_account_owner = SalesforceField()
    forecast_user_id = SalesforceField()
    may_forecast_manager_share = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    developer_name = SalesforceField()
    portal_account_id = SalesforceField()
    portal_type = SalesforceField()
    portal_account_owner_id = SalesforceField()


class SalesforceEvent(SalesforceEntityMixin, TimeStampedMixin):
    class Meta(SalesforceEntityMixin.Meta):
        abstract = False
        db_table = 'salesforce_event'

    who_id = SalesforceField(db_index=True)
    what_id = SalesforceField(db_index=True)
    who_count = SalesforceField()
    what_count = SalesforceField()
    subject = SalesforceField()
    is_all_day_event = SalesforceField()
    activity_date_time = SalesforceField()
    activity_date = SalesforceField()
    duration_in_minutes = SalesforceField()
    start_date_time = SalesforceField()
    end_date_time = SalesforceField()
    description = SalesforceField()
    account_id = SalesforceField(db_index=True)
    owner_id = SalesforceField(db_index=True)
    type = SalesforceField()
    is_private = SalesforceField()
    show_as = SalesforceField()
    is_child = SalesforceField()
    is_group_event = SalesforceField()
    group_event_type = SalesforceField()
    created_date = SalesforceField()
    created_by_id = SalesforceField()
    last_modified_date = SalesforceField()
    last_modified_by_id = SalesforceField()
    system_modstamp = SalesforceField()
    is_archived = SalesforceField()
    recurrence_activity_id = SalesforceField()
    is_recurrence = SalesforceField()
    recurrence_start_date_time = SalesforceField()
    recurrence_end_date_only = SalesforceField()
    recurrence_time_zone_sid_key = SalesforceField()
    recurrence_type = SalesforceField()
    recurrence_interval = SalesforceField()
    recurrence_day_of_week_mask = SalesforceField()
    recurrence_day_of_month = SalesforceField()
    recurrence_instance = SalesforceField()
    recurrence_month_of_year = SalesforceField()
    reminder_date_time = SalesforceField()
    is_reminder_set = SalesforceField()
    event_subtype = SalesforceField()
